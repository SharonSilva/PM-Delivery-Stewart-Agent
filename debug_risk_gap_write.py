import json
from datetime import datetime
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.risk_gap_service import detect_risk_gaps
from storage.risk_gap_approval_service import approve_and_write_risk_gap
from approval.write_gate import WriteBlockedError, execute_approved_write
from storage.risk_log_writer import write_risk_entry
from storage.db import get_connection, init_db

# Clean slate for this test
init_db()
conn = get_connection()
conn.execute("DELETE FROM proposals WHERE id IN ('RISK-GAP-T-003', 'RISK-GAP-T-004')")
conn.commit()
conn.close()

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()
snapshot = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))

with open("seed_data/risk_log.json") as f:
    before = json.load(f)
print(f"Risk log entries BEFORE: {len(before['risks'])}")

proposals = detect_risk_gaps(snapshot)
print(f"Proposals created: {[p.id for p in proposals]}")

# Approve and write ONE of them
approve_and_write_risk_gap(proposals[0].id, approver="andrea")

with open("seed_data/risk_log.json") as f:
    after = json.load(f)
print(f"Risk log entries AFTER approving {proposals[0].id}: {len(after['risks'])}")
print(f"New entry: {after['risks'][-1]}")

# Confirm the SECOND proposal (still pending, never approved) cannot write
try:
    execute_approved_write(proposals[1].id, write_risk_entry)
    print("FAIL: unapproved proposal was allowed to write!")
except WriteBlockedError as e:
    print(f"PASS: unapproved proposal correctly blocked: {e}")
