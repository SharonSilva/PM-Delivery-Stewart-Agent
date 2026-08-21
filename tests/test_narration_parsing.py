"""
Unit tests for storage.brief_narration_service._parse_narrated_brief -
the raw-LLM-response-to-structured-object parser. Tests specific
malformed-input edge cases directly, in isolation, with no LLM call
and no dependency on which response the model happens to produce on
a given run (that variability is exactly what eval/demo_malformed_output_handling.py
demonstrates live against the real retry loop - this file tests the
parsing function itself in isolation).
"""
import json
import pytest
from pydantic import ValidationError

from storage.brief_narration_service import _parse_narrated_brief


def test_parses_clean_json():
    """The simplest case: valid JSON, no markdown fences."""
    raw = '{"lines": [{"text": "Delivered", "source_ref": "T-001"}]}'
    result = _parse_narrated_brief(raw)
    assert len(result.lines) == 1
    assert result.lines[0].source_ref == "T-001"


def test_strips_markdown_json_fence():
    """The model sometimes wraps its JSON in ```json ... ``` fences
    despite being told not to - the parser must strip these."""
    raw = '```json\n{"lines": [{"text": "Delivered", "source_ref": "T-001"}]}\n```'
    result = _parse_narrated_brief(raw)
    assert len(result.lines) == 1


def test_strips_plain_markdown_fence():
    """Same as above but with a bare ``` fence, no 'json' language tag."""
    raw = '```\n{"lines": [{"text": "Delivered", "source_ref": "T-001"}]}\n```'
    result = _parse_narrated_brief(raw)
    assert len(result.lines) == 1


def test_strips_surrounding_whitespace():
    """Leading/trailing whitespace around the JSON must not break parsing."""
    raw = '   \n  {"lines": [{"text": "Delivered", "source_ref": "T-001"}]}  \n  '
    result = _parse_narrated_brief(raw)
    assert len(result.lines) == 1


def test_completely_invalid_json_raises():
    """Genuinely malformed JSON (not just fenced) must raise, not
    silently return something. The caller's retry loop is
    responsible for catching this and retrying - the parser itself
    must fail loudly."""
    raw = "this is not json at all"
    with pytest.raises(json.JSONDecodeError):
        _parse_narrated_brief(raw)


def test_valid_json_wrong_schema_raises():
    """JSON that parses but doesn't match the NarratedBrief schema
    (e.g. missing the required 'lines' key) must raise a validation
    error, not silently produce an empty/wrong object."""
    raw = '{"not_lines": "wrong shape"}'
    with pytest.raises(ValidationError):
        _parse_narrated_brief(raw)


def test_empty_lines_list_is_valid():
    """An empty lines list is a valid, parseable response - not an
    error condition on its own."""
    raw = '{"lines": []}'
    result = _parse_narrated_brief(raw)
    assert result.lines == []
