from datetime import datetime
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.weekly_report_service import extract_weekly_report_facts
from storage.weekly_report_assembly_service import generate_weekly_report

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()
snapshot = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))

facts = extract_weekly_report_facts(snapshot)
report = generate_weekly_report(facts)
print(report.render())
