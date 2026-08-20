from datetime import datetime
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.risk_log_store import load_risk_log
from storage.proposal_store import get_all_proposals

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()
snapshot = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))

blocked_items = [item for item in snapshot.items if item.status == "Blocked"]
print(f"Blocked items in snapshot: {[i.id for i in blocked_items]}")

risks = load_risk_log()
risk_item_ids = {r["item_id"] for r in risks if r.get("item_id")}
print(f"Item IDs already in risk log: {risk_item_ids}")

all_proposals = get_all_proposals()
print(f"All existing proposals ({len(all_proposals)}):")
for p in all_proposals:
    print(f"  id={p.id}, type={p.proposal_type}, source_ref={p.source_ref}, status={p.status.value}")
