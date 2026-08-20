"""
Golden Case 4: gap-detection precision. Self-cleaning - removes any
prior risk_gap_fill proposals for the blockers under test before
running, so repeated harness runs give a true result each time
rather than being skewed by leftover state from a previous run.
"""
from datetime import datetime

from storage.db import get_connection, init_db
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.risk_gap_service import detect_risk_gaps
from approval.approval_service import reject

ANCHOR = datetime(2026, 8, 18, 18, 0, 0)
KNOWN_BLOCKERS = {"T-003", "T-004"}  # per seed data - the only two currently blocked
KNOWN_ALREADY_IN_RISK_LOG = {"T-002", "T-018"}  # from risk_log.json's item_id fields


def _reset_test_proposals():
    """Clears prior risk_gap_fill proposals for our known blockers,
    so this golden case is idempotent across repeated harness runs."""
    init_db()
    conn = get_connection()
    for item_id in KNOWN_BLOCKERS:
        conn.execute(
            "DELETE FROM proposals WHERE id = ?",
            (f"RISK-GAP-{item_id}",)
        )
    conn.commit()
    conn.close()


def golden_case_4_gap_detection():
    """Assert that the two blockers absent from the risk log are
    proposed and the present ones are not. Then reject one, re-run,
    and assert no duplicate proposal appears."""
    _reset_test_proposals()

    tracker = MockTrackerAdapter()
    codehost = MockCodeHostAdapter()
    chat = MockChatAdapter()
    snapshot = take_snapshot(tracker, codehost, chat, as_of=ANCHOR)

    # First run: should propose exactly the known blockers
    proposals = detect_risk_gaps(snapshot)
    proposed_ids = {p.source_ref for p in proposals}

    precision_correct = proposed_ids == KNOWN_BLOCKERS
    detail_parts = [f"first run proposed {proposed_ids}, expected {KNOWN_BLOCKERS}"]

    # Reject one, re-run - should NOT re-propose it
    if proposals:
        reject(proposals[0].id, approver="eval-harness")
        rerun_proposals = detect_risk_gaps(snapshot)
        no_duplicate = len(rerun_proposals) == 0
        detail_parts.append(f"after rejecting {proposals[0].id} and re-running: {len(rerun_proposals)} new proposals (expected 0)")
    else:
        no_duplicate = False
        detail_parts.append("no proposals to reject - first run produced none")

    passed = precision_correct and no_duplicate
    target = True
    measured = passed
    detail = "; ".join(detail_parts)

    return passed, measured, target, detail
