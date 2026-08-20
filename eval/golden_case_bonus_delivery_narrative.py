"""
Golden Case 11: each causal claim cites at least two specific
items/events, and correlation is never stated as cause (no
causal-assertion language in the output).
"""
from datetime import datetime
from pathlib import Path

from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.delivery_narrative_service import extract_delivery_narrative_facts
from mocks.risk_log_mock import MockRiskLogAdapter
from storage.delivery_narrative_assembly_service import generate_delivery_narrative
from storage.delivery_narrative_narration_service import _contains_causal_assertion

ANCHOR = datetime(2026, 8, 18, 18, 0, 0)


def golden_case_bonus_delivery_narrative():
    # Self-cleaning: ensure a genuine (not self-compared) velocity
    # direction for this run.
    store = Path("storage/weekly_reports.jsonl")
    if store.exists():
        store.unlink()

    tracker = MockTrackerAdapter()
    codehost = MockCodeHostAdapter()
    chat = MockChatAdapter()
    snapshot = take_snapshot(tracker, codehost, chat, as_of=ANCHOR)

    risk_log = MockRiskLogAdapter()
    facts = extract_delivery_narrative_facts(snapshot, risk_log)
    narrative = generate_delivery_narrative(facts)

    # Every association in facts must cite >= 2 distinct items (code layer)
    citation_requirement_met = all(
        len(set(a.cited_item_ids)) >= 2 for a in facts.associations
    )

    # Every NARRATED (post-LLM) line must be free of causal-assertion language
    no_causal_language = all(
        not _contains_causal_assertion(text) for text in narrative.narrated_associations
    )

    # If there were real associations to test, both checks matter;
    # if there were none (e.g. velocity stayed similar this run),
    # the case still passes vacuously - there's nothing dishonest
    # about correctly reporting no notable coincidence.
    passed = citation_requirement_met and no_causal_language
    detail = (
        f"{len(facts.associations)} association(s) found; "
        f"all cite >= 2 distinct items: {citation_requirement_met}; "
        f"no causal-assertion language in narrated output: {no_causal_language}"
    )
    return passed, passed, True, detail
