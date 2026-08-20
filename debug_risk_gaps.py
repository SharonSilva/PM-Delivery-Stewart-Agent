from datetime import datetime
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.risk_gap_service import detect_risk_gaps

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()

snapshot = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))
proposals = detect_risk_gaps(snapshot)

print(f"{len(proposals)} new proposals created:")
for p in proposals:
    print(f"  {p.id}: item={p.source_ref}, owner={p.original_payload['suggested_owner']}, status={p.status.value}")
