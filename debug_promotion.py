from datetime import datetime
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.blocker_promotion_service import detect_promotion_candidates
from storage.db import get_connection, init_db

# Clean slate
init_db()
conn = get_connection()
conn.execute("DELETE FROM proposals WHERE proposal_type = 'blocker_promotion'")
conn.commit()
conn.close()

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()
snapshot = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))

print("=== Threshold = 2 days (config default) ===")
proposals = detect_promotion_candidates(snapshot, threshold_days=2)
for p in proposals:
    print(f"  {p.id}: {p.original_payload['days_blocked']} days blocked")

# Clean again to test independently with a different threshold
conn = get_connection()
conn.execute("DELETE FROM proposals WHERE proposal_type = 'blocker_promotion'")
conn.commit()
conn.close()

print("=== Threshold = 5 days ===")
proposals = detect_promotion_candidates(snapshot, threshold_days=5)
print(f"  {len(proposals)} proposals (expected 0, since T-003 is only 4 days blocked)")
