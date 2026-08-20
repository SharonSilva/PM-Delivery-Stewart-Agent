from datetime import datetime
from pathlib import Path

# Clean slate for this test
store = Path("storage/weekly_reports.jsonl")
if store.exists():
    store.unlink()

from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.weekly_report_service import extract_weekly_report_facts

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()
snapshot = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))

facts = extract_weekly_report_facts(snapshot)

print(f"Week: {facts.week_start} to {facts.week_end} ({facts.elapsed_days} elapsed days)")
print(f"Completed this period: {facts.items_completed_count} items, rate={facts.velocity_rate}/day")
print(f"Prior period: {facts.prior_period_label}, {facts.prior_period_items_completed} items, rate={facts.prior_period_velocity_rate}")
print(f"Scope added mid-sprint: {[s.item_id for s in facts.scope_added_mid_sprint]} (expected T-019, T-020)")
print(f"Top risks: {[(r.id, r.impact) for r in facts.top_risks]}")
print(f"Decisions needed (no owner): {[r.id for r in facts.decisions_needed]} (expected R-003)")
