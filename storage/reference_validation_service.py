from models.brief_output import NarratedBrief, BriefLine


class ValidatedLine(BriefLine):
    """A BriefLine after validation, with the outcome attached."""
    supported: bool


def validate_lines(
    narrated: NarratedBrief,
    item_titles: dict[str, str],
    extra_known_refs: set[str] = None,
) -> list[ValidatedLine]:
    """Reference-or-drop: every line's source_ref must resolve to
    something real. Generic across capabilities - takes the item
    ID -> title map directly rather than requiring a specific facts
    type, so both the morning brief (BriefFacts) and the EOD
    summary (EODDeltaFacts) can share this one validation function.

    extra_known_refs covers non-item references (e.g. person names
    for the no-activity case in the morning brief)."""
    known_refs = set(item_titles.keys())
    if extra_known_refs:
        known_refs.update(extra_known_refs)

    validated = []
    for line in narrated.lines:
        is_known_ref = line.source_ref in known_refs

        title_check_passed = True
        if line.source_ref in item_titles:
            real_title = item_titles[line.source_ref]
            title_check_passed = real_title.lower() in line.text.lower()

        supported = is_known_ref and title_check_passed
        validated.append(ValidatedLine(
            text=line.text,
            source_ref=line.source_ref,
            supported=supported,
        ))
    return validated


def drop_unsupported(validated: list[ValidatedLine]) -> list[ValidatedLine]:
    """Strips unsupported lines entirely, per reference-or-drop."""
    return [line for line in validated if line.supported]
