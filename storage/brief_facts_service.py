from datetime import date, datetime, timedelta

from models.snapshot import Snapshot
from models.brief_facts import BriefFacts, PersonStatus, BlockerFact
from storage.risk_log_store import load_risk_log

SPRINT_2_START = date(2026, 8, 17)
SPRINT_2_END = date(2026, 8, 28)
SPRINT_2_NAME = "Sprint 2"

ACTIVITY_WINDOW_DAYS = 2  # "no activity for 2 days" per the brief's difficulty spec


def _days_blocked(item_id: str, transitions: list, as_of: datetime) -> int:
    blocked_transitions = [
        t for t in transitions
        if t.item_id == item_id and t.to_status == "Blocked" and t.timestamp <= as_of
    ]
    if not blocked_transitions:
        return 0
    latest_block = max(blocked_transitions, key=lambda t: t.timestamp)
    return (as_of - latest_block.timestamp).days


def _had_recent_activity(person: str, snapshot: Snapshot, as_of: datetime) -> bool:
    """True if this person has a transition, commit, or message
    within ACTIVITY_WINDOW_DAYS of as_of. This is what 'activity'
    actually means for the no-activity-assignee difficulty —
    having an assigned item that merely sits in some status is
    NOT activity."""
    window_start = as_of - timedelta(days=ACTIVITY_WINDOW_DAYS)

    person_item_ids = {i.id for i in snapshot.items if i.assignee == person}

    for t in snapshot.transitions:
        if t.item_id in person_item_ids and window_start <= t.timestamp <= as_of:
            return True
    for c in snapshot.commits:
        if c.author == person and window_start <= c.timestamp <= as_of:
            return True
    for m in snapshot.messages:
        if m.author == person and window_start <= m.timestamp <= as_of:
            return True
    return False


def extract_brief_facts(snapshot: Snapshot) -> BriefFacts:
    risks = load_risk_log()
    risk_item_ids = {r["item_id"] for r in risks if r.get("item_id")}

    as_of = snapshot.taken_at
    today = as_of.date()
    sprint_day = (today - SPRINT_2_START).days + 1
    sprint_total_days = (SPRINT_2_END - SPRINT_2_START).days + 1

    people_map: dict[str, PersonStatus] = {}
    for item in snapshot.items:
        assignee = item.assignee
        if assignee is None:
            continue
        if assignee not in people_map:
            people_map[assignee] = PersonStatus(person=assignee, had_activity=False)
        p = people_map[assignee]
        if item.status == "Done":
            p.delivered.append(item.id)
        elif item.status == "Blocked":
            p.blocked.append(item.id)
        elif item.status == "Open":
            p.pending.append(item.id)
        else:
            p.committed.append(item.id)

    for person, p in people_map.items():
        p.had_activity = _had_recent_activity(person, snapshot, as_of)

    blockers = []
    for item in snapshot.items:
        if item.status == "Blocked":
            days = _days_blocked(item.id, snapshot.transitions, as_of)
            blockers.append(BlockerFact(
                item_id=item.id,
                title=item.title,
                assignee=item.assignee,
                days_blocked=days,
                in_risk_log=item.id in risk_item_ids,
            ))
    blockers.sort(key=lambda b: b.days_blocked, reverse=True)

    return BriefFacts(
        sprint_name=SPRINT_2_NAME,
        sprint_day=sprint_day,
        sprint_total_days=sprint_total_days,
        people=list(people_map.values()),
        blockers=blockers,
    )
