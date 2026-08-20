from datetime import datetime
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.weekly_report_service import extract_weekly_report_facts
from storage.weekly_narration_service import (
    narrate_progress, narrate_scope_change, narrate_top_risks,
    narrate_decisions_needed, narrate_velocity,
)

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()
snapshot = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))
facts = extract_weekly_report_facts(snapshot)

print("=== Progress ===")
print(narrate_progress(facts))
print("\n=== Scope change ===")
print(narrate_scope_change(facts))
print("\n=== Top risks ===")
for line in narrate_top_risks(facts):
    print(f"  {line}")
print("\n=== Decisions needed ===")
for line in narrate_decisions_needed(facts):
    print(f"  {line}")
print("\n=== Velocity ===")
print(narrate_velocity(facts))
