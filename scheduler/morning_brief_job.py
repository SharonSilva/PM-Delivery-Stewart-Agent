from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.brief_facts_service import extract_brief_facts
from storage.morning_brief_service import generate_morning_brief
from scheduler.clock import clock


def run_morning_brief_job() -> str:
    """The actual job body the scheduler fires. Uses the shared
    clock so demo overrides apply automatically - no separate
    demo-only code path."""
    tracker = MockTrackerAdapter()
    codehost = MockCodeHostAdapter()
    chat = MockChatAdapter()

    snapshot = take_snapshot(tracker, codehost, chat, as_of=clock.now())
    facts = extract_brief_facts(snapshot)
    brief = generate_morning_brief(facts)

    rendered = brief.render()
    print(rendered)
    return rendered
