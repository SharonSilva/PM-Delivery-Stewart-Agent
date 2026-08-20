from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.sprint_planning_service import extract_sprint_planning_facts
from storage.sprint_planning_assembly_service import generate_sprint_planning_pack
from scheduler.clock import clock


def run_sprint_planning_job() -> str:
    """Fires before planning. Produces a DRAFT only - no write path
    exists at all, per spec ('never applied to the tracker
    automatically')."""
    tracker = MockTrackerAdapter()
    codehost = MockCodeHostAdapter()
    chat = MockChatAdapter()

    snapshot = take_snapshot(tracker, codehost, chat, as_of=clock.now())
    facts = extract_sprint_planning_facts(snapshot)
    pack = generate_sprint_planning_pack(facts)

    rendered = pack.render()
    print(rendered)
    return rendered
