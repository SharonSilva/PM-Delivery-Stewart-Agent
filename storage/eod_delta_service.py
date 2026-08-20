from models.snapshot import Snapshot
from models.eod_delta import ItemDelta, EODDeltaFacts
from storage.brief_facts_service import SPRINT_2_NAME, SPRINT_2_START


def compute_eod_delta(morning_snapshot: Snapshot, eod_snapshot: Snapshot) -> EODDeltaFacts:
    """Compares two snapshots of the same day. For each item with
    activity in the window, reports it as shipped / newly_blocked /
    changed_other, collapsing flaps into one accurate line. Items
    that were Open at both boundaries with zero activity go into
    still_pending, kept separate from 'changed' so the summary
    doesn't imply movement that didn't happen."""

    morning_status = {item.id: item.status for item in morning_snapshot.items}
    eod_status = {item.id: item.status for item in eod_snapshot.items}
    item_titles = {item.id: item.title for item in eod_snapshot.items}

    all_ids = set(morning_status.keys()) | set(eod_status.keys())

    shipped, newly_blocked, changed_other, still_pending = [], [], [], []

    for item_id in all_ids:
        m_status = morning_status.get(item_id, "(did not exist)")
        e_status = eod_status.get(item_id, "(no longer present)")

        transitions_in_window = [
            t for t in eod_snapshot.transitions
            if t.item_id == item_id
            and morning_snapshot.taken_at < t.timestamp <= eod_snapshot.taken_at
        ]
        flapped = len(transitions_in_window) > 1

        if not transitions_in_window:
            if m_status == "Open" and e_status == "Open":
                still_pending.append(item_id)
            continue

        delta = ItemDelta(
            item_id=item_id,
            title=item_titles.get(item_id, "(unknown)"),
            morning_status=m_status,
            eod_status=e_status,
            flapped=flapped,
            transition_count=len(transitions_in_window),
        )

        if e_status == "Done":
            shipped.append(delta)
        elif e_status == "Blocked":
            newly_blocked.append(delta)
        else:
            changed_other.append(delta)

    today = eod_snapshot.taken_at.date()
    sprint_day = (today - SPRINT_2_START).days + 1

    return EODDeltaFacts(
        sprint_name=SPRINT_2_NAME,
        sprint_day=sprint_day,
        morning_taken_at=morning_snapshot.taken_at.isoformat(),
        eod_taken_at=eod_snapshot.taken_at.isoformat(),
        shipped=shipped,
        newly_blocked=newly_blocked,
        changed_other=changed_other,
        still_pending=still_pending,
        item_titles=item_titles,
    )
