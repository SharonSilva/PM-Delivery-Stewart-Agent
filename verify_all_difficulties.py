from datetime import datetime
from mocks.tracker_mock import MockTrackerAdapter
from mocks.codehost_mock import MockCodeHostAdapter
from mocks.chat_mock import MockChatAdapter
from storage.snapshot_service import take_snapshot
from storage.brief_facts_service import extract_brief_facts

tracker = MockTrackerAdapter()
codehost = MockCodeHostAdapter()
chat = MockChatAdapter()
snapshot = take_snapshot(tracker, codehost, chat, as_of=datetime(2026, 8, 18, 18, 0, 0))
facts = extract_brief_facts(snapshot)

print("=== #1: T-003 4-day blocker, no risk entry ===")
t003 = next((b for b in facts.blockers if b.item_id == "T-003"), None)
print(f"  {t003.days_blocked if t003 else 'MISSING'} days blocked, in_risk_log={t003.in_risk_log if t003 else None} (expected 4, False)")

print("=== #2: T-004 1-day blocker control ===")
t004 = next((b for b in facts.blockers if b.item_id == "T-004"), None)
print(f"  {t004.days_blocked if t004 else 'MISSING'} days blocked (expected 1)")

print("=== #3: T-005 same-day flap ===")
priya_s = next((p for p in facts.people if p.person == "Priya Sharma"), None)
print(f"  T-005 in Priya Sharma's delivered: {'T-005' in priya_s.delivered if priya_s else 'MISSING'} (expected True)")

print("=== #4: Sam Okafor zero activity ===")
sam = next((p for p in facts.people if p.person == "Sam Okafor"), None)
print(f"  had_activity={sam.had_activity if sam else 'MISSING'} (expected False)")

print("=== #5: T-006 unassigned ===")
t006_found = any("T-006" in (p.pending + p.committed + p.delivered + p.blocked) for p in facts.people)
print(f"  T-006 appears under a person: {t006_found} (expected False)")

print("=== #6: T-019/T-020 mid-sprint additions ===")
items = tracker.get_items()
t019 = next((i for i in items if i.id == "T-019"), None)
t020 = next((i for i in items if i.id == "T-020"), None)
print(f"  T-019 created={t019.created_at if t019 else 'MISSING'}, T-020 created={t020.created_at if t020 else 'MISSING'} (expected 2026-08-18)")

print("=== #7: commit with no item ref ===")
commits = codehost.get_commits()
unlinked = [c for c in commits if c.item_id is None]
print(f"  {len(unlinked)} unlinked commits (expected >= 1): {[c.hash for c in unlinked]}")

print("=== #8: T-011 never transitioned, referenced by commit ===")
transitions = tracker.get_transitions()
t011_transitions = [t for t in transitions if t.item_id == "T-011"]
t011_commits = [c for c in commits if c.item_id == "T-011"]
print(f"  T-011 transitions: {len(t011_transitions)} (expected 0), referenced by commits: {[c.hash for c in t011_commits]} (expected non-empty)")

print("=== #9: T-007 free-text status ===")
t007 = next((i for i in items if i.id == "T-007"), None)
print(f"  T-007 status='{t007.status if t007 else 'MISSING'}' (expected 'waiting on design')")

print("=== #10: C-002 ambiguous due date ===")
from storage.commitment_store import load_commitments
commitments = load_commitments()
c002 = next((c for c in commitments if c.id == "C-002"), None)
print(f"  C-002 due_date={c002.due_date if c002 else 'MISSING'} (expected None), due_date_text='{c002.due_date_text if c002 else None}' (expected 'by Friday')")
