from storage.prompt_loader import load_prompt
import json

from pydantic import ValidationError

from llm.client import call_llm
from models.weekly_report import WeeklyReportFacts
from models.brief_output import NarratedBrief, BriefLine

MAX_RETRIES = 3


def _parse_narrated_brief(raw_response: str) -> NarratedBrief:
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    parsed = json.loads(cleaned)
    return NarratedBrief.model_validate(parsed)


def _call_with_retry(prompt: str) -> NarratedBrief:
    last_error = None
    for attempt in range(MAX_RETRIES):
        # Only use the cache on the first attempt - a retry that
        # replays the same cached malformed response is not a real
        # retry at all. Force a fresh generation on every subsequent attempt.
        raw = call_llm(prompt, use_cache=(attempt == 0))
        try:
            return _parse_narrated_brief(raw)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            continue
    raise RuntimeError(f"LLM failed after {MAX_RETRIES} attempts: {last_error}")


def narrate_progress(facts: WeeklyReportFacts) -> str:
    prompt = load_prompt(
        "weekly_progress_summary",
        SPRINT_NAME=facts.sprint_name,
        WEEK_START=facts.week_start,
        WEEK_END=facts.week_end,
        ELAPSED_DAYS=facts.elapsed_days,
        ITEMS_COMPLETED_COUNT=facts.items_completed_count,
    )
    result = _call_with_retry(prompt)
    text = result.lines[0].text if result.lines else f"{facts.items_completed_count} items completed over {facts.elapsed_days} day(s)."
    return text


def narrate_scope_change(facts: WeeklyReportFacts) -> str:
    if not facts.scope_added_mid_sprint:
        return "No items were added to scope mid-sprint."

    prompt = load_prompt(
        "weekly_scope_change",
        SCOPE_COUNT=len(facts.scope_added_mid_sprint),
    )
    result = _call_with_retry(prompt)
    summary = result.lines[0].text if result.lines else f"{len(facts.scope_added_mid_sprint)} item(s) added mid-sprint."

    details = "; ".join(
        f'{s.item_id} ("{facts.item_titles.get(s.item_id, s.title)}")'
        for s in facts.scope_added_mid_sprint
    )
    return f"{summary} Added: {details}."


def narrate_top_risks(facts: WeeklyReportFacts) -> list[str]:
    return [f"[{r.impact}] {r.description}" for r in facts.top_risks]


def narrate_decisions_needed(facts: WeeklyReportFacts) -> list[str]:
    if not facts.decisions_needed:
        return ["No risks currently lack an assigned owner."]
    return [
        f"{r.id}: {r.description} (no owner assigned - flagged as needing a decision)"
        for r in facts.decisions_needed
    ]


def _classify_velocity_change(current_rate: float, prior_rate: float) -> str:
    """Computed in code, not judged by the model."""
    if prior_rate == 0:
        return "increased" if current_rate > 0 else "stayed at zero"
    ratio = current_rate / prior_rate
    if ratio >= 1.2:
        return "increased"
    elif ratio <= 0.8:
        return "decreased"
    return "stayed similar"


def narrate_velocity(facts: WeeklyReportFacts) -> str:
    """The DIRECTION is computed in code via a real threshold.
    We ASK the model to phrase it, but we do not trust the model's
    output blindly: if the model's sentence doesn't actually
    contain the computed direction word, we discard the model's
    text and use a deterministic, fully code-generated sentence
    instead. This caught a real failure during testing - the model
    was told the direction was 'increased' and still wrote
    'stayed similar', contradicting a given fact outright."""
    if facts.prior_period_velocity_rate is None:
        return "No prior period is available for a velocity comparison."

    direction = _classify_velocity_change(facts.velocity_rate, facts.prior_period_velocity_rate)

    deterministic_fallback = (
        f"Velocity {direction} this period: {facts.velocity_rate} items/day, "
        f"compared to {facts.prior_period_label}'s {facts.prior_period_velocity_rate} items/day."
    )

    prompt = load_prompt(
        "weekly_velocity",
        DIRECTION=direction,
        VELOCITY_RATE=facts.velocity_rate,
        ELAPSED_DAYS=facts.elapsed_days,
        PRIOR_PERIOD_LABEL=facts.prior_period_label,
        PRIOR_VELOCITY_RATE=facts.prior_period_velocity_rate,
        PRIOR_PERIOD_DAYS=facts.prior_period_days,
    )

    result = _call_with_retry(prompt)
    if not result.lines:
        return deterministic_fallback

    text = result.lines[0].text

    # Validate: does the model's text actually agree with the
    # computed direction? If not, discard it - never let an
    # unverified claim reach the report.
    direction_words = {
        "increased": ["increas", "up", "higher", "faster", "rose"],
        "decreased": ["decreas", "down", "lower", "slower", "dropped", "fell"],
        "stayed similar": ["similar", "steady", "consistent", "unchanged", "same"],
        "stayed at zero": ["zero", "no progress", "none"],
    }
    keywords = direction_words.get(direction, [])
    text_lower = text.lower()
    agrees = any(kw in text_lower for kw in keywords)

    return text if agrees else deterministic_fallback
