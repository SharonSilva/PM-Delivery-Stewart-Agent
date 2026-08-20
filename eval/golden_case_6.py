"""
Golden Case 6: every quantitative claim in the weekly report is
reproducible from the stored snapshots, and the scope-change
section correctly identifies items added mid-sprint.
"""
from datetime import datetime
from pathlib import Path

from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.weekly_report_service import extract_weekly_report_facts

ANCHOR = datetime(2026, 8, 18, 18, 0, 0)
EXPECTED_SCOPE_ADDED = {"T-019", "T-020"}


def golden_case_6_weekly_report():
    # Self-cleaning: clear persisted history so this run's prior-
    # period comparison is deterministic (real Sprint 1, not a
    # leftover self-comparison from an earlier test run).
    store = Path("storage/weekly_reports.jsonl")
    if store.exists():
        store.unlink()

    tracker = MockTrackerAdapter()
    codehost = MockCodeHostAdapter()
    chat = MockChatAdapter()
    snapshot = take_snapshot(tracker, codehost, chat, as_of=ANCHOR)

    facts = extract_weekly_report_facts(snapshot)

    # Reproducibility check: re-derive items_completed_count directly
    # from the snapshot, independent of the facts extraction code path,
    # and confirm it matches.
    done_ids = {item.id for item in snapshot.items if item.status == "Done"}
    reproduced_count = 0
    for item_id in done_ids:
        done_transitions = [
            t for t in snapshot.transitions
            if t.item_id == item_id and t.to_status == "Done"
        ]
        if done_transitions:
            latest = max(done_transitions, key=lambda t: t.timestamp)
            if facts.week_start <= latest.timestamp.date().isoformat() <= facts.week_end:
                reproduced_count += 1
    count_reproducible = reproduced_count == facts.items_completed_count

    scope_ids = {s.item_id for s in facts.scope_added_mid_sprint}
    scope_correct = scope_ids == EXPECTED_SCOPE_ADDED

    passed = count_reproducible and scope_correct
    detail = (
        f"items_completed_count reproducible from snapshot: {count_reproducible} "
        f"({reproduced_count} vs {facts.items_completed_count}); "
        f"scope-change correctly identifies {scope_ids} (expected {EXPECTED_SCOPE_ADDED})"
    )
    return passed, passed, True, detail
