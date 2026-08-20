from datetime import datetime
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.sprint_planning_service import extract_sprint_planning_facts

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()
snapshot = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))

facts = extract_sprint_planning_facts(snapshot)

print(f"Reference sprint: {facts.reference_sprint_name} ({facts.reference_sprint_start} to {facts.reference_sprint_end})")
print(f"\nCarry-over ({len(facts.carry_over)}):")
for c in facts.carry_over:
    print(f"  {c.item_id} ({c.title}): status_at_sprint_end={c.status_at_sprint_end}, assignee={c.assignee}")

print(f"\nCapacity note: {facts.capacity_is_assumption_note}")

print(f"\nCandidate slice ({len(facts.candidate_slice)}):")
for s in facts.candidate_slice:
    print(f"  {s.item_id} ({s.title}, priority={s.priority}): {s.reasoning}")

print(f"\nRemaining backlog: {len(facts.ready_backlog)} items")
