from datetime import datetime
from scheduler.clock import clock
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from scheduler.eod_summary_job import run_eod_summary_job

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()

# Simulate the morning job having already run today
take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 9, 0, 0))

# Now simulate the EOD job firing via the clock
clock.set_override(datetime(2026, 8, 18, 18, 0, 0))
run_eod_summary_job()
