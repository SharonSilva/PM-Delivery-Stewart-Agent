from datetime import datetime
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.risk_gap_service import detect_risk_gaps
from approval.approval_service import reject

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()
snapshot = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))

# Re-run detection with pending proposals already existing - should create 0 new
proposals = detect_risk_gaps(snapshot)
print(f"Re-run with pending proposals already existing: {len(proposals)} new proposals (expected 0)")

# Reject T-003's proposal
reject("RISK-GAP-T-003", approver="andrea")
print("Rejected RISK-GAP-T-003")

# Re-run again - T-003 should NOT be re-proposed since it was already proposed (now rejected)
proposals = detect_risk_gaps(snapshot)
print(f"Re-run after rejection: {len(proposals)} new proposals (expected 0)")
