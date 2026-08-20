from datetime import datetime
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.eod_delta_service import compute_eod_delta
from storage.eod_summary_service import generate_eod_summary

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()

morning = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 9, 0, 0))
eod = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))

facts = compute_eod_delta(morning, eod)
summary = generate_eod_summary(facts)
print(summary.render())
