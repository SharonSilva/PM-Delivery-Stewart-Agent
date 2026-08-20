from datetime import date, timedelta

from models.commitment import Commitment
from models.notification import NotificationRecord
from storage.commitment_store import load_commitments

NUDGE_WINDOW_DAYS = 2       # nudge when due within this many days
ESCALATION_THRESHOLD_DAYS = 3  # escalate once this many days overdue
DAILY_NUDGE_CAP_PER_PERSON = 1


def _todays_nudge_count(person: str, today: date, notifications: list[dict]) -> int:
    """Counts nudges already sent to this person today, reading
    from the notification log itself - the log IS the cap counter,
    no separate state to keep in sync."""
    count = 0
    for n in notifications:
        if n["kind"] != "nudge" or n["recipient"] != person:
            continue
        n_date = date.fromisoformat(n["timestamp"][:10])
        if n_date == today:
            count += 1
    return count


def _read_notification_log(log_path: str = "storage/notifications.jsonl") -> list[dict]:
    import json
    from pathlib import Path
    path = Path(log_path)
    if not path.exists():
        return []
    entries = []
    with open(path) as f:
        for line in f:
            entries.append(json.loads(line))
    return entries


def classify_commitment(commitment: Commitment, today: date) -> str:
    """Returns one of: 'ambiguous', 'ok', 'nudge_due', 'overdue',
    'escalate'. Ambiguous due dates are surfaced explicitly, never
    silently resolved or skipped."""
    if commitment.due_date is None:
        return "ambiguous"

    days_until_due = (commitment.due_date - today).days

    if days_until_due < 0:
        overdue_days = -days_until_due
        if overdue_days >= ESCALATION_THRESHOLD_DAYS:
            return "escalate"
        return "overdue"
    elif days_until_due <= NUDGE_WINDOW_DAYS:
        return "nudge_due"
    return "ok"


def run_commitment_check(as_of_date: date, notification_adapter) -> dict:
    """Runs the full daily check: classifies every commitment,
    sends nudges (capped per person per day) and escalations
    (visible to lead, per spec), and returns an ageing view.
    """

    commitments = load_commitments()
    existing_log = _read_notification_log()

    ageing_view = []
    nudges_sent = []
    escalations = []
    capped_skips = []

    for c in commitments:
        classification = classify_commitment(c, as_of_date)
        ageing_view.append({"id": c.id, "person": c.person, "classification": classification})

        if classification == "nudge_due" or classification == "overdue":
            count_today = _todays_nudge_count(c.person, as_of_date, existing_log)
            if count_today >= DAILY_NUDGE_CAP_PER_PERSON:
                capped_skips.append(c.id)
                continue

            record = NotificationRecord(
                id=f"NUDGE-{c.id}-{as_of_date.isoformat()}",
                kind="nudge",
                recipient=c.person,
                commitment_id=c.id,
                message=f"Reminder: '{c.description}' ({c.id}) is due {c.due_date}.",
                timestamp=as_of_date.isoformat() + "T09:00:00",
            )
            notification_adapter.write(record)
            nudges_sent.append(record)
            existing_log.append(record.model_dump(mode="json"))

        elif classification == "escalate":
            record = NotificationRecord(
                id=f"ESCALATE-{c.id}-{as_of_date.isoformat()}",
                kind="escalation",
                recipient="delivery-lead",
                commitment_id=c.id,
                message=(
                    f"ESCALATION: '{c.description}' ({c.id}) for {c.person} is significantly "
                    f"overdue (due {c.due_date}). Visible to lead before any client-facing comms."
                ),
                timestamp=as_of_date.isoformat() + "T09:00:00",
            )
            notification_adapter.write(record)
            escalations.append(record)
            existing_log.append(record.model_dump(mode="json"))

    return {
        "ageing_view": ageing_view,
        "nudges_sent": nudges_sent,
        "escalations": escalations,
        "capped_skips": capped_skips,
    }
