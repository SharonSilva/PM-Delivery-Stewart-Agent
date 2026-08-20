from datetime import date

from adapters.adapter_factory import get_notification_adapter
from storage.commitment_tracking_service import run_commitment_check
from scheduler.clock import clock


def run_commitment_check_job():
    """Daily job: checks all commitments, sends nudges (capped)
    and escalations, per the shared clock so demo overrides apply."""
    today = clock.now().date()
    notification_adapter = get_notification_adapter()
    result = run_commitment_check(as_of_date=today, notification_adapter=notification_adapter)
    print(f"[Commitments] {len(result['nudges_sent'])} nudge(s), {len(result['escalations'])} escalation(s), {len(result['capped_skips'])} capped.")
    for entry in result["ageing_view"]:
        print(f"  {entry['id']} ({entry['person']}): {entry['classification']}")
    return result
