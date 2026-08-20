from adapters.adapter_factory import get_tracker_adapter, get_codehost_adapter, get_chat_adapter
from storage.snapshot_service import take_snapshot
from storage.brief_facts_service import extract_brief_facts
from storage.morning_brief_service import generate_morning_brief
from storage.risk_gap_service import detect_risk_gaps
from scheduler.clock import clock


def run_morning_brief_job() -> str:
    """Fires each morning: takes a snapshot, generates the morning
    brief, then immediately runs risk-gap detection on the same
    snapshot - P4's trigger is 'after the morning read', so it
    belongs right here rather than as a separate scheduled job."""
    tracker = get_tracker_adapter()
    codehost = get_codehost_adapter()
    chat = get_chat_adapter()

    snapshot = take_snapshot(tracker, codehost, chat, as_of=clock.now())
    facts = extract_brief_facts(snapshot)
    brief = generate_morning_brief(facts)

    rendered = brief.render()
    print(rendered)

    gap_proposals = detect_risk_gaps(snapshot)
    if gap_proposals:
        print(f"\n[Risk-gap detection] {len(gap_proposals)} new proposal(s) awaiting approval:")
        for p in gap_proposals:
            print(f"  {p.id}: {p.original_payload['description']}")
    else:
        print("\n[Risk-gap detection] No new gaps found.")

    return rendered
