"""
Golden Case 3: delta correctness. Hand-labeled expected change set
for the real Aug 18 09:00-18:00 window, independently derived by
parsing seed_data/tracker_items.json directly (not by calling
compute_eod_delta or any extraction code). Assert the EOD delta
names exactly this set, measured as precision and recall.

Hand-labeled ground truth (verified by direct inspection of raw
transitions, including T-005's same-day flap - Done->In Progress->
Blocked->Done, ending Done despite 3 transitions):
  shipped (ends Done):        {T-005}
  newly_blocked (ends Blocked): {} (T-005 passed through Blocked
                                     but did not END there)
  changed_other (ends elsewhere but changed): {T-018, T-035}
"""
from datetime import datetime

from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.eod_delta_service import compute_eod_delta

MORNING = datetime(2026, 8, 18, 9, 0, 0)
EOD = datetime(2026, 8, 18, 18, 0, 0)

EXPECTED_SHIPPED = {"T-005"}
EXPECTED_NEWLY_BLOCKED = set()
EXPECTED_CHANGED_OTHER = {"T-018", "T-035"}


def _precision_recall(expected: set, actual: set):
    if not actual and not expected:
        return 1.0, 1.0
    tp = len(expected & actual)
    precision = tp / len(actual) if actual else (1.0 if not expected else 0.0)
    recall = tp / len(expected) if expected else (1.0 if not actual else 0.0)
    return precision, recall


def golden_case_3_delta_correctness():
    tracker = MockTrackerAdapter()
    codehost = MockCodeHostAdapter()
    chat = MockChatAdapter()

    morning_snapshot = take_snapshot(tracker, codehost, chat, as_of=MORNING)
    eod_snapshot = take_snapshot(tracker, codehost, chat, as_of=EOD)

    delta = compute_eod_delta(morning_snapshot, eod_snapshot)

    actual_shipped = {d.item_id for d in delta.shipped}
    actual_newly_blocked = {d.item_id for d in delta.newly_blocked}
    actual_changed_other = {d.item_id for d in delta.changed_other}

    p1, r1 = _precision_recall(EXPECTED_SHIPPED, actual_shipped)
    p2, r2 = _precision_recall(EXPECTED_NEWLY_BLOCKED, actual_newly_blocked)
    p3, r3 = _precision_recall(EXPECTED_CHANGED_OTHER, actual_changed_other)

    all_precise = p1 == 1.0 and p2 == 1.0 and p3 == 1.0
    all_recalled = r1 == 1.0 and r2 == 1.0 and r3 == 1.0

    # Explicitly re-verify T-005's flap is captured correctly - the
    # deliberate difficulty this case exists to catch.
    t005 = next((d for d in delta.shipped if d.item_id == "T-005"), None)
    flap_correct = t005 is not None and t005.flapped is True and t005.transition_count == 3

    passed = all_precise and all_recalled and flap_correct
    detail = (
        f"shipped P/R={p1}/{r1} (got {actual_shipped}, expected {EXPECTED_SHIPPED}); "
        f"newly_blocked P/R={p2}/{r2} (got {actual_newly_blocked}); "
        f"changed_other P/R={p3}/{r3} (got {actual_changed_other}, expected {EXPECTED_CHANGED_OTHER}); "
        f"T-005 flap correctly captured (flapped=True, 3 transitions): {flap_correct}"
    )
    return passed, passed, True, detail
