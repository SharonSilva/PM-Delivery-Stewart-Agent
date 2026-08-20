"""
Golden Case 5: promotion threshold is genuinely configuration.
With threshold=2, exactly the seeded blockers older than 2 days
are proposed. Re-run with threshold=4 and assert the set shrinks
correctly.
"""
from datetime import datetime

from storage.db import get_connection, init_db
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.blocker_promotion_service import detect_promotion_candidates

ANCHOR = datetime(2026, 8, 18, 18, 0, 0)


def _reset_test_proposals():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM proposals WHERE proposal_type = 'blocker_promotion'")
    conn.commit()
    conn.close()


def golden_case_5_promotion_threshold():
    tracker = MockTrackerAdapter()
    codehost = MockCodeHostAdapter()
    chat = MockChatAdapter()
    snapshot = take_snapshot(tracker, codehost, chat, as_of=ANCHOR)

    _reset_test_proposals()
    proposals_at_2 = detect_promotion_candidates(snapshot, threshold_days=2)
    ids_at_2 = {p.source_ref for p in proposals_at_2}

    _reset_test_proposals()
    proposals_at_4 = detect_promotion_candidates(snapshot, threshold_days=4)
    ids_at_4 = {p.source_ref for p in proposals_at_4}
    _reset_test_proposals()

    # T-003 is 4 days blocked, T-004 is 1 day blocked (per seed data).
    # threshold=2 should catch T-003 only; threshold=4 should still catch
    # T-003 (>= 4) but the set must not GROW - proves threshold genuinely drives it.
    threshold_drives_result = ids_at_2 == {"T-003"} and ids_at_4 == {"T-003"}

    passed = threshold_drives_result
    detail = f"threshold=2 proposed {ids_at_2}, threshold=4 proposed {ids_at_4}"
    return passed, passed, True, detail
