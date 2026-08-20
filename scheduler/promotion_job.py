from adapters.adapter_factory import get_tracker_adapter, get_codehost_adapter, get_chat_adapter, get_risk_log_adapter, get_proposal_store_adapter
from storage.snapshot_service import take_snapshot
from storage.blocker_promotion_service import detect_promotion_candidates
from scheduler.clock import clock


def run_promotion_check_job() -> list:
    """Daily job: checks all currently-blocked items against the
    configured age threshold and creates draft promotion proposals
    for any that qualify and aren't already proposed."""
    tracker = get_tracker_adapter()
    codehost = get_codehost_adapter()
    chat = get_chat_adapter()

    snapshot = take_snapshot(tracker, codehost, chat, as_of=clock.now())
    risk_log = get_risk_log_adapter()
    store = get_proposal_store_adapter()
    proposals = detect_promotion_candidates(snapshot, risk_log, store)

    if proposals:
        print(f"[Blocker promotion] {len(proposals)} new promotion proposal(s):")
        for p in proposals:
            print(f"  {p.id}: {p.original_payload['mitigation_draft']}")
    else:
        print("[Blocker promotion] No blockers exceed the promotion threshold.")

    return proposals
