"""
Unit tests for storage.reference_validation_service - the
reference-or-drop mechanism. Tests the function in isolation with
hand-constructed inputs, not real seed data or an LLM call (that's
what the golden cases in eval/ are for) - this targets specific
parsing/validation edge cases directly.
"""
from models.brief_output import NarratedBrief, BriefLine
from storage.reference_validation_service import validate_lines, drop_unsupported


def test_valid_reference_is_supported():
    """A line whose source_ref exists and whose text contains the
    real title should be marked supported."""
    narrated = NarratedBrief(lines=[
        BriefLine(text='Delivered: T-001 ("Set up CI pipeline")', source_ref="T-001"),
    ])
    item_titles = {"T-001": "Set up CI pipeline"}

    result = validate_lines(narrated, item_titles)

    assert len(result) == 1
    assert result[0].supported is True


def test_unknown_reference_is_unsupported():
    """A source_ref that doesn't exist in item_titles or
    extra_known_refs must be flagged unsupported, not silently
    accepted."""
    narrated = NarratedBrief(lines=[
        BriefLine(text="Delivered: T-999 (\"Fabricated item\")", source_ref="T-999"),
    ])
    item_titles = {"T-001": "Set up CI pipeline"}

    result = validate_lines(narrated, item_titles)

    assert result[0].supported is False


def test_wrong_title_for_real_reference_is_unsupported():
    """A source_ref that IS real, but whose text doesn't actually
    contain that item's real title, must be flagged unsupported -
    this catches a model that cites a real ID but describes the
    wrong thing."""
    narrated = NarratedBrief(lines=[
        BriefLine(text="Delivered: T-001 (\"Some other title entirely\")", source_ref="T-001"),
    ])
    item_titles = {"T-001": "Set up CI pipeline"}

    result = validate_lines(narrated, item_titles)

    assert result[0].supported is False


def test_extra_known_refs_allows_non_item_references():
    """A source_ref that isn't an item ID (e.g. a person's name for
    the no-activity case) is supported if explicitly passed via
    extra_known_refs."""
    narrated = NarratedBrief(lines=[
        BriefLine(text="Sam Okafor: no update found since the last check-in.", source_ref="Sam Okafor"),
    ])
    item_titles = {}

    result = validate_lines(narrated, item_titles, extra_known_refs={"Sam Okafor"})

    assert result[0].supported is True


def test_drop_unsupported_strips_only_unsupported_lines():
    """drop_unsupported must remove unsupported lines and keep
    supported ones - not drop everything, not keep everything."""
    narrated = NarratedBrief(lines=[
        BriefLine(text='Delivered: T-001 ("Set up CI pipeline")', source_ref="T-001"),
        BriefLine(text="Delivered: T-999 (\"Fabricated\")", source_ref="T-999"),
    ])
    item_titles = {"T-001": "Set up CI pipeline"}

    validated = validate_lines(narrated, item_titles)
    dropped = drop_unsupported(validated)

    assert len(validated) == 2
    assert len(dropped) == 1
    assert dropped[0].source_ref == "T-001"


def test_empty_lines_produces_empty_result():
    """An empty NarratedBrief should validate to an empty list, not
    raise an error."""
    narrated = NarratedBrief(lines=[])
    result = validate_lines(narrated, {})
    assert result == []
