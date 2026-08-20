from datetime import datetime
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.delivery_narrative_service import extract_delivery_narrative_facts

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()
snapshot = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))

facts = extract_delivery_narrative_facts(snapshot)

print(f"Period: {facts.reference_period_label} ({facts.reference_period_start} to {facts.reference_period_end})")
print(f"Velocity: {facts.velocity_this_period}, direction={facts.velocity_direction}")
print(f"\nBlocker periods overlapping window ({len(facts.blocker_periods)}):")
for b in facts.blocker_periods:
    print(f"  {b.item_id}: {b.blocked_from} to {b.blocked_until or 'ongoing'} ({b.days_blocked} days)")
print(f"\nScope events in window ({len(facts.scope_events)}):")
for s in facts.scope_events:
    print(f"  {s.item_id} created {s.event_date}")
print(f"\nAssociations ({len(facts.associations)}):")
for a in facts.associations:
    print(f"  cites {a.cited_item_ids}: {a.description}")
