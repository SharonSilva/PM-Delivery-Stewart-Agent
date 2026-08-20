from datetime import datetime, timedelta

from adapters.adapter_factory import get_tracker_adapter, get_codehost_adapter, get_chat_adapter
from storage.snapshot_service import take_snapshot
from storage.snapshot_store import get_all_snapshots
from storage.eod_delta_service import compute_eod_delta
from storage.eod_summary_service import generate_eod_summary
from scheduler.clock import clock


def run_eod_summary_job() -> str:
    """Fires at end of day. Uses the shared clock, same as the
    morning job, so demo overrides apply automatically. Needs
    BOTH a morning snapshot and a fresh EOD snapshot - it looks
    back through today's persisted snapshots to find the earliest
    one taken today, rather than assuming one exists in memory."""
    tracker = get_tracker_adapter()
    codehost = get_codehost_adapter()
    chat = get_chat_adapter()

    now = clock.now()
    eod_snapshot = take_snapshot(tracker, codehost, chat, as_of=now)

    today_start = datetime(now.year, now.month, now.day)
    todays_snapshots = [
        s for s in get_all_snapshots()
        if today_start <= s.taken_at <= now
    ]
    if len(todays_snapshots) < 2:
        message = "No morning snapshot found for today yet - cannot compute a delta."
        print(message)
        return message

    morning_snapshot = min(todays_snapshots, key=lambda s: s.taken_at)
    delta = compute_eod_delta(morning_snapshot, eod_snapshot)
    summary = generate_eod_summary(delta)
    output = summary.render()
    print(output)
    return output
