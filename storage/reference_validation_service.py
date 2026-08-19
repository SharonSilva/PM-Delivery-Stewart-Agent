from models.brief_facts import BriefFacts
from models.brief_output import NarratedBrief, BriefLine


class ValidatedLine(BriefLine):
    """A BriefLine after validation, with the outcome attached."""
    supported: bool


def _known_references(facts: BriefFacts) -> set[str]:
    """Every ID a source_ref is allowed to point to: item IDs plus
    person names (for the no-activity case, which references a
    person rather than an item)."""
    refs = set(facts.item_titles.keys())
    refs.update(p.person for p in facts.people)
    return refs


def validate_lines(narrated: NarratedBrief, facts: BriefFacts) -> list[ValidatedLine]:
    """Reference-or-drop: every line's source_ref must resolve to
    something real. This is the hard validation step called for in
    the design notes — a distinct, inspectable function, not a hope
    baked into the prompt."""
    known_refs = _known_references(facts)
    validated = []

    for line in narrated.lines:
        is_known_ref = line.source_ref in known_refs

        # If the ref is a real item, the real title must actually
        # appear in the line text - catches the fabrication case
        # where source_ref is valid but the description drifted.
        title_check_passed = True
        if line.source_ref in facts.item_titles:
            real_title = facts.item_titles[line.source_ref]
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