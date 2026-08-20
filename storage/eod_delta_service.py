import json
from pathlib import Path

from models.snapshot import Snapshot
from models.eod_delta import ItemDelta, EODDeltaFacts, MeetingOutcomeNote
from storage.brief_facts_service import SPRINT_2_NAME, SPRINT_2_START


def _load_meeting_outcomes(path: str = "seed_data/meeting_outcomes.json") -> list[dict]:
    with open(Path(path)) as f:
        data = json.load(f)
    return data["meeting_outcomes"]


def _evidence_for_item(item_id: str, eod_snapshot: Snapshot, window_start, window_end):
    """Real commit messages and chat texts referencing this item,
    strictly within the delta window - this is what the narration
    stage will use instead of inventing what happened."""
    commit_msgs = [
        c.message for c in eod_snapshot.commits
        if c.item_id == item_id and window_start < c.timestamp <= window_end
    ]
    chat_texts = [
        m.text for m in eod_snapshot.messages
        if m.item_id == item_id and window_start < m.timestamp <= window_end
    ]
    return commit_msgs, chat_texts


def compute_eod_delta(morning_snapshot: Snapshot, eod_snapshot: Snapshot) -> EODDeltaFacts:
    """Compares two snapshots of the same day, enriched with real
    commit/message evidence per changed item, plus any meeting
    outcomes that fell within the window."""

    morning_status = {item.id: item.status for item in morning_snapshot.items}
    eod_status = {item.id: item.status for item in eod_snapshot.items}
    item_titles = {item.id: item.title for item in eod_snapshot.items}

    all_ids = set(morning_status.keys()) | set(eod_status.keys())
    window_start, window_end = morning_snapshot.taken_at, eod_snapshot.taken_at

    shipped, newly_blocked, changed_other, still_pending = [], [], [], []

    for item_id in all_ids:
        m_status = morning_status.get(item_id, "(did not exist)")
        e_status = eod_status.get(item_id, "(no longer present)")

        transitions_in_window = [
            t for t in eod_snapshot.transitions
            if t.item_id == item_id and window_start < t.timestamp <= window_end
        ]
        flapped = len(transitions_in_window) > 1

        if not transitions_in_window:
            if m_status == "Open" and e_status == "Open":
                still_pending.append(item_id)
            continue

        commit_msgs, chat_texts = _evidence_for_item(item_id, eod_snapshot, window_start, window_end)

        delta = ItemDelta(
            item_id=item_id,
            title=item_titles.get(item_id, "(unknown)"),
            morning_status=m_status,
            eod_status=e_status,
            flapped=flapped,
            transition_count=len(transitions_in_window),
            commit_messages=commit_msgs,
            chat_excerpts=chat_texts,
        )

        if e_status == "Done":
            shipped.append(delta)
        elif e_status == "Blocked":
            newly_blocked.append(delta)
        else:
            changed_other.append(delta)

    # Meeting outcomes that fell within today's window
    meeting_notes = []
    for mo in _load_meeting_outcomes():
        meeting_dt = mo["meeting_date"]
        from datetime import datetime as _dt
        meeting_ts = _dt.fromisoformat(meeting_dt)
        if window_start < meeting_ts <= window_end:
            meeting_notes.append(MeetingOutcomeNote(
                meeting_id=mo["id"],
                consent=mo["consent"],
                decision_texts=[d["text"] for d in mo["decisions"]],
            ))

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
        meeting_outcomes_today=meeting_notes,
    )
