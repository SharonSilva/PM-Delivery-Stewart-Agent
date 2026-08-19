import json

from pydantic import ValidationError

from llm.client import call_llm
from models.brief_facts import PersonStatus, BlockerFact
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
        raw = call_llm(prompt, use_cache=True)
        try:
            return _parse_narrated_brief(raw)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            continue
    raise RuntimeError(
        f"LLM failed to produce valid structured output after {MAX_RETRIES} attempts: {last_error}"
    )


def _format_item_list(item_ids: list[str], titles: dict[str, str]) -> str:
    """Renders item IDs with their REAL titles, so the model has
    actual content to work from instead of inventing descriptions."""
    if not item_ids:
        return "(none)"
    return "; ".join(f"{iid} (\"{titles.get(iid, 'unknown title')}\")" for iid in item_ids)


def narrate_person_status(person: PersonStatus, item_titles: dict[str, str]) -> NarratedBrief:
    if not person.had_activity:
        return NarratedBrief(lines=[
            BriefLine(
                text=f"{person.person}: no update found since the last check-in.",
                source_ref=person.person,
            )
        ])

    prompt = f"""You are writing one section of a daily project brief for {person.person}.
Return ONLY valid JSON, no markdown fences, no explanation, matching this exact shape:
{{"lines": [{{"text": "...", "source_ref": "..."}}]}}

STRICT RULE: use ONLY the item titles given below. Do not invent, guess, or add any
detail about what the work involves beyond the title text provided. If a title is
generic, keep your line generic too — do not embellish it with invented specifics.

Delivered (done): {_format_item_list(person.delivered, item_titles)}
Currently working on: {_format_item_list(person.committed, item_titles)}
Not yet started: {_format_item_list(person.pending, item_titles)}
Blocked: {_format_item_list(person.blocked, item_titles)}

For each item listed above (skip any section marked "(none)"), write one short line
using its real title, and set source_ref to that item's ID exactly."""

    return _call_with_retry(prompt)
