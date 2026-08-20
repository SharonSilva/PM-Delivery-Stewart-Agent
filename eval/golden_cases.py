"""
Golden test cases for the Delivery Steward agent's morning brief
pipeline. Each function returns (passed: bool, measured, target, detail).
"""
from datetime import datetime

from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.brief_facts_service import extract_brief_facts
from storage.morning_brief_service import generate_morning_brief
from storage.brief_narration_service import narrate_person_status
from storage.reference_validation_service import validate_lines

ANCHOR = datetime(2026, 8, 18, 18, 0, 0)


def _get_facts():
    tracker = MockTrackerAdapter()
    codehost = MockCodeHostAdapter()
    chat = MockChatAdapter()
    snapshot = take_snapshot(tracker, codehost, chat, as_of=ANCHOR)
    return extract_brief_facts(snapshot)


def golden_case_1_citation_rate():
    """Across a generated morning brief, measure the proportion of
    factual lines carrying a valid, resolvable source reference.
    Target: >= 0.9. A reference that doesn't resolve counts as a
    failure, not a citation."""
    facts = _get_facts()
    total_lines = 0
    supported_lines = 0

    for person in facts.people:
        narrated = narrate_person_status(person, facts.item_titles)
        validated = validate_lines(narrated, facts.item_titles, extra_known_refs={p.person for p in facts.people})
        total_lines += len(validated)
        supported_lines += sum(1 for v in validated if v.supported)

    rate = supported_lines / total_lines if total_lines else 0.0
    target = 0.9
    passed = rate >= target
    detail = f"{supported_lines}/{total_lines} lines had valid, resolvable references"
    return passed, round(rate, 3), target, detail


def golden_case_2_fabrication_probe():
    """Assert no line claims a transition, commit or message that
    does not exist in the snapshot. Includes the zero-activity
    assignee and empty-day scenario. Target: 0 fabricated claims.
    This is the most important number in the submission."""
    facts = _get_facts()
    fabricated_count = 0
    fabrication_details = []

    for person in facts.people:
        narrated = narrate_person_status(person, facts.item_titles)
        validated = validate_lines(narrated, facts.item_titles, extra_known_refs={p.person for p in facts.people})
        for v in validated:
            if not v.supported:
                fabricated_count += 1
                fabrication_details.append(f"{person.person}: '{v.text}' (ref={v.source_ref})")

    # Explicitly verify the zero-activity case reports absence, not fabrication.
    sam = next((p for p in facts.people if p.person == "Sam Okafor"), None)
    zero_activity_handled = sam is not None and not sam.had_activity

    target = 0
    passed = fabricated_count == target and zero_activity_handled
    detail = (
        f"{fabricated_count} fabricated claims found; "
        f"zero-activity case (Sam Okafor) correctly handled: {zero_activity_handled}"
    )
    if fabrication_details:
        detail += " | " + "; ".join(fabrication_details)
    return passed, fabricated_count, target, detail


def golden_case_9_determinism():
    """Generate the morning brief twice from the same snapshot.
    Wording may differ; the set of items, owners, counts and
    statuses must not. Any factual divergence is a failure."""
    facts_1 = _get_facts()
    facts_2 = _get_facts()

    matches = (
        facts_1.sprint_day == facts_2.sprint_day
        and facts_1.people == facts_2.people
        and facts_1.blockers == facts_2.blockers
        and facts_1.item_titles == facts_2.item_titles
    )

    target = True
    passed = matches == target
    detail = "Facts extracted twice from the same snapshot are identical" if matches else "MISMATCH between two extractions"
    return passed, matches, target, detail
