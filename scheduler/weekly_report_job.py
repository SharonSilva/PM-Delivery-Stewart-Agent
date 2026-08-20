from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.weekly_report_service import extract_weekly_report_facts
from storage.weekly_report_assembly_service import generate_weekly_report
from scheduler.clock import clock


def run_weekly_report_job() -> str:
    """Weekly job. Produces a DRAFT report only - never sends.
    Per spec, the delivery lead reviews, edits, and sends it."""
    tracker = MockTrackerAdapter()
    codehost = MockCodeHostAdapter()
    chat = MockChatAdapter()

    snapshot = take_snapshot(tracker, codehost, chat, as_of=clock.now())
    facts = extract_weekly_report_facts(snapshot)
    report = generate_weekly_report(facts)

    rendered = report.render()
    print(rendered)  # stands in for "posted for lead review" until a real UI exists
    return rendered
