import json
from datetime import datetime
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.blocker_promotion_service import detect_promotion_candidates
from storage.promotion_approval_service import approve_and_write_promotion
from storage.db import get_connection, init_db

init_db()
conn = get_connection()
conn.execute("DELETE FROM proposals WHERE proposal_type = 'blocker_promotion'")
conn.commit()
conn.close()

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()
snapshot = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))

with open("seed_data/risk_log.json") as f:
    before = json.load(f)
print(f"Risk log entries BEFORE: {len(before['risks'])}")

proposals = detect_promotion_candidates(snapshot)
print(f"Promotion proposals: {[p.id for p in proposals]}")

approve_and_write_promotion(proposals[0].id, approver="andrea")

with open("seed_data/risk_log.json") as f:
    after = json.load(f)
print(f"Risk log entries AFTER: {len(after['risks'])}")
print(f"New entry: {after['risks'][-1]}")
