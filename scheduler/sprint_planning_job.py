from adapters.adapter_factory import get_tracker_adapter, get_codehost_adapter, get_chat_adapter
from storage.snapshot_service import take_snapshot
from storage.sprint_planning_service import extract_sprint_planning_facts
from storage.sprint_planning_assembly_service import generate_sprint_planning_pack
from scheduler.clock import clock


def run_sprint_planning_job() -> str:
    """Fires before planning. Produces a DRAFT only - no write path
    exists at all, per spec ('never applied to the tracker
    automatically')."""
    tracker = get_tracker_adapter()
    codehost = get_codehost_adapter()
    chat = get_chat_adapter()

    snapshot = take_snapshot(tracker, codehost, chat, as_of=clock.now())
    facts = extract_sprint_planning_facts(snapshot)
    pack = generate_sprint_planning_pack(facts)

    rendered = pack.render()
    print(rendered)
    return rendered
