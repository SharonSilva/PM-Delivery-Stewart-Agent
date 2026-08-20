"""
Golden Case 10 (P10): the carry-over list is exactly correct
against the seeded history. Any capacity assumption is stated as
an assumption. Also proves capacity is genuine configuration, not
a hardcoded literal, by comparing two different capacity values.
"""
from datetime import datetime

from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
import storage.sprint_planning_service as sps

ANCHOR = datetime(2026, 8, 18, 18, 0, 0)


def golden_case_bonus_sprint_planning():
    tracker = MockTrackerAdapter()
    codehost = MockCodeHostAdapter()
    chat = MockChatAdapter()
    snapshot = take_snapshot(tracker, codehost, chat, as_of=ANCHOR)

    facts_12 = sps.extract_sprint_planning_facts(snapshot)
    carry_over_ids_12 = {c.item_id for c in facts_12.carry_over}
    assumption_stated = "[ASSUMPTION]" in facts_12.capacity_is_assumption_note

    # Independently re-derive carry-over straight from raw
    # transitions (not reusing the extraction code path) to prove
    # genuine reproducibility, same pattern as Golden Case 6.
    sprint_end_dt = datetime(2026, 8, 14, 23, 59, 59)
    reproduced_carry_over = set()
    for item in snapshot.items:
        if item.created_at.date() > sps.REFERENCE_SPRINT_END:
            continue
        relevant = [t for t in snapshot.transitions if t.item_id == item.id and t.timestamp <= sprint_end_dt]
        if not relevant:
            continue
        latest = max(relevant, key=lambda t: t.timestamp)
        if latest.to_status != "Done":
            reproduced_carry_over.add(item.id)
    carry_over_reproducible = reproduced_carry_over == carry_over_ids_12

    # Prove capacity is genuine config: different values change the
    # candidate slice size, and the slice never exceeds remaining capacity.
    original = sps.TEAM_CAPACITY_ITEMS_PER_SPRINT
    sps.TEAM_CAPACITY_ITEMS_PER_SPRINT = 25
    facts_25 = sps.extract_sprint_planning_facts(snapshot)
    sps.TEAM_CAPACITY_ITEMS_PER_SPRINT = original

    capacity_drives_result = (
        len(facts_12.candidate_slice) == 0
        and len(facts_25.candidate_slice) == max(25 - len(facts_25.carry_over), 0)
        and len(facts_25.candidate_slice) > len(facts_12.candidate_slice)
    )

    passed = carry_over_reproducible and assumption_stated and capacity_drives_result
    detail = (
        f"carry-over reproducible from raw transitions: {carry_over_reproducible} "
        f"({len(carry_over_ids_12)} items); assumption explicitly stated: {assumption_stated}; "
        f"capacity genuinely drives result (12->{len(facts_12.candidate_slice)} slice, "
        f"25->{len(facts_25.candidate_slice)} slice): {capacity_drives_result}"
    )
    return passed, passed, True, detail
