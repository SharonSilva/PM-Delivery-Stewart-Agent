"""
Unit tests for storage.delivery_narrative_narration_service._contains_causal_assertion -
the guard that prevents P11 from asserting cause instead of
correlation. Tests the pure detection function directly with
hand-crafted inputs, isolated from any LLM call.
"""
from storage.delivery_narrative_narration_service import _contains_causal_assertion


def test_detects_caused():
    assert _contains_causal_assertion("T-003 caused the slowdown") is True


def test_detects_led_to():
    assert _contains_causal_assertion("The blocker led to a delay") is True


def test_detects_resulted_in():
    assert _contains_causal_assertion("This resulted in slower delivery") is True


def test_detects_due_to():
    assert _contains_causal_assertion("Velocity dropped due to the blocker") is True


def test_detects_because_of():
    assert _contains_causal_assertion("Delayed because of the schema migration") is True


def test_allows_coincidence_language():
    """The hedge language the guard is meant to preserve must NOT
    trigger a false positive."""
    assert _contains_causal_assertion("T-003 coincided with the change") is False


def test_allows_neutral_description():
    assert _contains_causal_assertion("Velocity increased during this period") is False


def test_case_insensitive():
    """The guard must not be bypassable just by capitalization."""
    assert _contains_causal_assertion("This CAUSED the slowdown") is True
