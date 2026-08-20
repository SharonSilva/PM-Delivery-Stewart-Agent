from datetime import datetime
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.delivery_narrative_service import extract_delivery_narrative_facts
from storage.delivery_narrative_narration_service import narrate_association, _contains_causal_assertion

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()
snapshot = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))

facts = extract_delivery_narrative_facts(snapshot)

print("=== Real association narration ===")
for a in facts.associations:
    print(f"Original: {a.description}")
    narrated = narrate_association(a)
    print(f"Narrated: {narrated}")
    all_cited_present = all(item_id in narrated for item_id in a.cited_item_ids)
    print(f"All cited items present in narrated text: {all_cited_present}")
    print(f"Contains causal-assertion language: {_contains_causal_assertion(narrated)}")

print("\n=== Guard function unit test ===")
print(_contains_causal_assertion("T-003 caused the slowdown"))  # expect True
print(_contains_causal_assertion("T-003 coincided with the change"))  # expect False
