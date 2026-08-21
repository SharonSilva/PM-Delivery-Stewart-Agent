import json

from pydantic import ValidationError

from llm.client import call_llm
from models.brief_facts import PersonStatus
from storage.prompt_loader import load_prompt
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


def _format_item_list(item_ids: list[str], titles: dict[str, str]) -> str:
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

    prompt = load_prompt(
        "morning_brief_person_status",
        PERSON_NAME=person.person,
        DELIVERED=_format_item_list(person.delivered, item_titles),
        COMMITTED=_format_item_list(person.committed, item_titles),
        PENDING=_format_item_list(person.pending, item_titles),
        BLOCKED=_format_item_list(person.blocked, item_titles),
    )

    result = _call_with_retry(prompt)

    # Substitute in the real title ourselves, in code - the model never
    # has to correctly escape a quoted title inside its own JSON string.
    final_lines = []
    covered_ids = set()
    for line in result.lines:
        title = item_titles.get(line.source_ref)
        if title:
            text = f'{line.text.strip().rstrip(":")}: {line.source_ref} ("{title}")'
            covered_ids.add(line.source_ref)
        else:
            text = line.text
        final_lines.append(BriefLine(text=text, source_ref=line.source_ref))

    # Completeness check: the model can silently under-generate (stop
    # early, skip an item) with no error raised anywhere. Reference-or-
    # drop only checks that what WAS said is real - this checks the
    # reverse: that everything real actually got said. Any item the
    # model omitted gets a plain, code-generated fallback line instead
    # of silently vanishing from the brief.
    category_labels = {
        "delivered": "Delivered",
        "committed": "Currently working on",
        "pending": "Not yet started",
        "blocked": "Blocked",
    }
    for field, label in category_labels.items():
        for item_id in getattr(person, field):
            if item_id not in covered_ids:
                title = item_titles.get(item_id, "(unknown)")
                final_lines.append(BriefLine(
                    text=f'{label}: {item_id} ("{title}")',
                    source_ref=item_id,
                ))
                covered_ids.add(item_id)

    return NarratedBrief(lines=final_lines)
