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

print(f"Sprint day: {delta.sprint_day}")
print(f"Shipped ({len(delta.shipped)}):")
for d in delta.shipped:
    print(f"  {d.item_id} ({d.title}): {d.morning_status} -> {d.eod_status}, flapped={d.flapped}, transitions={d.transition_count}")
print(f"Newly blocked ({len(delta.newly_blocked)}):")
for d in delta.newly_blocked:
    print(f"  {d.item_id} ({d.title}): {d.morning_status} -> {d.eod_status}, flapped={d.flapped}")
print(f"Changed other ({len(delta.changed_other)}):")
for d in delta.changed_other:
    print(f"  {d.item_id} ({d.title}): {d.morning_status} -> {d.eod_status}, flapped={d.flapped}")
print(f"Still pending: {len(delta.still_pending)} items")

t005 = next((d for d in delta.shipped + delta.newly_blocked + delta.changed_other if d.item_id == "T-005"), None)
print()
print("T-005 (flap item) found:", t005 is not None and t005.flapped)
