from datetime import date, datetime

from models.snapshot import Snapshot
from models.sprint_planning import CarryOverItem, CandidateItem, SprintPlanningFacts
from config.scheduler_config import TEAM_CAPACITY_ITEMS_PER_SPRINT

REFERENCE_SPRINT_NAME = "Sprint 1"
REFERENCE_SPRINT_START = date(2026, 8, 3)
REFERENCE_SPRINT_END = date(2026, 8, 14)

_PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


def _status_as_of(item_id: str, transitions: list, as_of: datetime) -> str | None:
    """Replays transitions up to (and including) as_of and returns
    the status that was true AT THAT MOMENT - not the item's
    current status today. This is what lets carry-over be computed
    against the sprint's real close date, not today's state."""
    relevant = [t for t in transitions if t.item_id == item_id and t.timestamp <= as_of]
    if not relevant:
        return None  # didn't exist yet as of that date
    latest = max(relevant, key=lambda t: t.timestamp)
    return latest.to_status


def extract_sprint_planning_facts(snapshot: Snapshot) -> SprintPlanningFacts:
    sprint_end_dt = datetime.combine(REFERENCE_SPRINT_END, datetime.max.time())
    item_titles = {item.id: item.title for item in snapshot.items}

    # Carry-over: items that existed by Sprint 1's close and were
    # NOT Done at that exact point in time.
    carry_over = []
    for item in snapshot.items:
        if item.created_at.date() > REFERENCE_SPRINT_END:
            continue  # didn't exist during the reference sprint
        status_then = _status_as_of(item.id, snapshot.transitions, sprint_end_dt)
        if status_then is not None and status_then != "Done":
            carry_over.append(CarryOverItem(
                item_id=item.id,
                title=item.title,
                status_at_sprint_end=status_then,
                assignee=item.assignee,
            ))

    capacity = TEAM_CAPACITY_ITEMS_PER_SPRINT
    capacity_note = (
        f"[ASSUMPTION] Stated capacity is {capacity} items per sprint. This planning "
        f"pack assumes each carry-over item consumes one unit of capacity 1-for-1, "
        f"the same as a new item - this is a simplification, not a measured fact, "
        f"and may not hold if carry-over items require significantly more or less "
        f"effort than average."
    )

    # Ready backlog: our disclosed proxy for "backlog" - Sprint 2
    # items that are still Open (scoped, not yet started).
    ready_backlog_items = [
        item for item in snapshot.items
        if item.status == "Open" and item.id not in {c.item_id for c in carry_over}
    ]
    ready_backlog_items.sort(key=lambda i: _PRIORITY_ORDER.get(i.priority, 3))

    ready_backlog = [
        CandidateItem(
            item_id=i.id, title=i.title, priority=i.priority,
            reasoning="In backlog, not yet selected for this candidate slice.",
        )
        for i in ready_backlog_items
    ]

    # Candidate slice: fill remaining capacity (capacity - carry_over
    # count) from ready backlog, highest priority first.
    remaining_capacity = max(capacity - len(carry_over), 0)
    slice_items = ready_backlog_items[:remaining_capacity]
    candidate_slice = [
        CandidateItem(
            item_id=i.id, title=i.title, priority=i.priority,
            reasoning=(
                f"Selected: priority={i.priority or 'unset'}, "
                f"fits within remaining capacity ({remaining_capacity} slot(s) "
                f"after {len(carry_over)} carry-over item(s))."
            ),
        )
        for i in slice_items
    ]
    remaining_backlog = [
        c for c in ready_backlog if c.item_id not in {s.item_id for s in candidate_slice}
    ]

    return SprintPlanningFacts(
        reference_sprint_name=REFERENCE_SPRINT_NAME,
        reference_sprint_start=REFERENCE_SPRINT_START.isoformat(),
        reference_sprint_end=REFERENCE_SPRINT_END.isoformat(),
        carry_over=carry_over,
        stated_capacity=capacity,
        capacity_is_assumption_note=capacity_note,
        ready_backlog=remaining_backlog,
        candidate_slice=candidate_slice,
        item_titles=item_titles,
    )
