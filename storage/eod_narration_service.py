from storage.prompt_loader import load_prompt
import json

from pydantic import ValidationError

from llm.client import call_llm
from models.eod_delta import ItemDelta
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
    raise RuntimeError(
        f"LLM failed to produce valid structured output after {MAX_RETRIES} attempts: {last_error}"
    )


def narrate_item_delta_raw(delta: ItemDelta) -> BriefLine:
    """Returns the raw narrated line (category description + real
    title substituted in) BEFORE validation - the caller is
    responsible for running it through reference-or-drop."""

    evidence_lines = []
    if delta.commit_messages:
        evidence_lines.append("Commit messages: " + "; ".join(delta.commit_messages))
    if delta.chat_excerpts:
        evidence_lines.append("Chat messages: " + "; ".join(delta.chat_excerpts))
    evidence_text = "\n".join(evidence_lines) if evidence_lines else "(no additional commit/chat evidence)"

    flap_note = (
        f"Note: this item changed status {delta.transition_count} times today before settling on its final status - "
        f"describe it as having moved through multiple states, not as unchanged."
        if delta.flapped else ""
    )

    prompt = load_prompt(
        "eod_item_delta",
        MORNING_STATUS=delta.morning_status,
        EOD_STATUS=delta.eod_status,
        FLAP_NOTE=flap_note,
        EVIDENCE_TEXT=evidence_text,
        ITEM_ID=delta.item_id,
    )

    result = _call_with_retry(prompt)
    if not result.lines:
        return BriefLine(text=f"{delta.morning_status} -> {delta.eod_status}", source_ref=delta.item_id)

    category_text = result.lines[0].text.strip().rstrip(":")
    full_text = f"{category_text}: {delta.item_id} (\"{delta.title}\")"
    return BriefLine(text=full_text, source_ref=delta.item_id)
