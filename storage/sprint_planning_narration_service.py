import json

from pydantic import ValidationError

from llm.client import call_llm
from models.sprint_planning import SprintPlanningFacts
from models.brief_output import NarratedBrief

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


def narrate_carry_over_summary(facts: SprintPlanningFacts) -> str:
    """One summarizing sentence about carry-over volume - the
    detailed list is rendered separately from real data, this is
    just a short framing line."""
    if not facts.carry_over:
        return f"No items carried over from {facts.reference_sprint_name}."
    prompt = f"""Write ONE short sentence noting that N items carried over from a prior sprint,
without naming them individually (they'll be listed separately).
Return ONLY valid JSON: {{"lines": [{{"text": "...", "source_ref": "carryover"}}]}}
N = {len(facts.carry_over)}"""
    result = _call_with_retry(prompt)
    return result.lines[0].text if result.lines else f"{len(facts.carry_over)} item(s) carried over."


def narrate_candidate_slice_summary(facts: SprintPlanningFacts) -> str:
    """Must handle the ZERO case honestly - this is not an error
    state, it's a genuine, important finding (team is over
    capacity) that must be stated plainly, not hidden.

    Deliberately does NOT call the LLM for the non-zero case. A
    prior version asked the model for a one-sentence intro and it
    fabricated a thematic justification ("aimed at enhancing user
    engagement") with no basis in the actual selected items. Since
    the real reasoning already lives in each item's own reasoning
    line below, a bare, code-generated count statement is both
    safer and sufficient - there is nothing genuine for an LLM to
    add here that isn't fabrication risk."""
    if not facts.candidate_slice:
        return (
            f"No new items are proposed for this candidate slice: {len(facts.carry_over)} "
            f"carry-over item(s) already meet or exceed the stated capacity of "
            f"{facts.stated_capacity}. Recommend reviewing carry-over before adding new scope."
        )
    return f"{len(facts.candidate_slice)} candidate item(s) proposed below, each with its own selection reasoning."
