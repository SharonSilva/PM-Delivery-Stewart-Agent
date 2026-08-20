from datetime import datetime

from models.proposal import Proposal, ProposalStatus
from approval.approval_service import submit_proposal, approve, reject, edit_then_approve
from approval.write_gate import execute_approved_write, WriteBlockedError

written_log = []

def fake_write(payload):
    written_log.append(payload)
    print(f"WROTE: {payload}")


# --- Test 1: pending proposal cannot write ---
p1 = Proposal(
    id="TEST-001",
    proposal_type="risk_gap_fill",
    source_ref="T-003",
    original_payload={"description": "OAuth flow blocked", "impact": "High"},
    created_at=datetime.now(),
)
submit_proposal(p1)

try:
    execute_approved_write("TEST-001", fake_write)
    print("FAIL: pending proposal was allowed to write!")
except WriteBlockedError as e:
    print(f"PASS: pending proposal correctly blocked: {e}")

# --- Test 2: rejected proposal cannot write ---
reject("TEST-001", approver="andrea")
try:
    execute_approved_write("TEST-001", fake_write)
    print("FAIL: rejected proposal was allowed to write!")
except WriteBlockedError as e:
    print(f"PASS: rejected proposal correctly blocked: {e}")

# --- Test 3: approved proposal DOES write ---
p2 = Proposal(
    id="TEST-002",
    proposal_type="risk_gap_fill",
    source_ref="T-004",
    original_payload={"description": "Pagination bug blocked", "impact": "Medium"},
    created_at=datetime.now(),
)
submit_proposal(p2)
approve("TEST-002", approver="andrea")
execute_approved_write("TEST-002", fake_write)
print(f"PASS: approved proposal wrote successfully. Log: {written_log}")

# --- Test 4: edit-then-approve applies the EDITED payload, not the original ---
p3 = Proposal(
    id="TEST-003",
    proposal_type="risk_gap_fill",
    source_ref="T-006",
    original_payload={"description": "unassigned item risk", "impact": "Low"},
    created_at=datetime.now(),
)
submit_proposal(p3)
edit_then_approve("TEST-003", approver="andrea", edited_payload={"description": "unassigned item risk - reassign urgently", "impact": "High"})
execute_approved_write("TEST-003", fake_write)
final = written_log[-1]
print(f"PASS: edit-then-approve applied EDITED payload: {final}")
assert final["impact"] == "High", "Edit did not take effect!"

print()
print("=== Audit trail check ===")
from storage.proposal_store import get_proposal
audit = get_proposal("TEST-003")
print(f"Approver: {audit.approver}")
print(f"Decided at: {audit.decided_at}")
print(f"Original: {audit.original_payload}")
print(f"Final (applied): {audit.final_payload}")
