from datetime import datetime
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.eod_delta_service import compute_eod_delta

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()

morning = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 9, 0, 0))
eod = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))
delta = compute_eod_delta(morning, eod)

t005 = next(d for d in delta.shipped if d.item_id == "T-005")
print(f"T-005 commit messages: {t005.commit_messages}")
print(f"T-005 chat excerpts: {t005.chat_excerpts}")
print()
print(f"Meeting outcomes today: {[m.meeting_id for m in delta.meeting_outcomes_today]}")
for m in delta.meeting_outcomes_today:
    print(f"  {m.meeting_id}: consent={m.consent}, decisions={m.decision_texts}")
