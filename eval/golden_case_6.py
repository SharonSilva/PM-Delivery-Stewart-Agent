"""
Golden Case 6: approval enforcement. An automated test attempting
writes for pending and rejected proposals directly against the
service layer - both must fail. Also asserts the audit record
captures approver, timestamp, original proposal, and applied
(final) payload correctly, including the edit-then-approve case
where original and final genuinely differ.
"""
from datetime import datetime

from models.proposal import Proposal, ProposalStatus
from mocks.proposal_store_sqlite import SqliteProposalStoreAdapter
from approval.approval_service import submit_proposal, approve, edit_then_approve, reject
from approval.write_gate import execute_approved_write, WriteBlockedError


def golden_case_6_approval_enforcement():
    store = SqliteProposalStoreAdapter()
    written = []

    def fake_write(payload):
        written.append(payload)

    results = {}

    # --- Pending: direct write attempt must fail ---
    p_pending = Proposal(
        id="GC6-PENDING", proposal_type="test", source_ref="X",
        original_payload={"a": 1}, created_at=datetime.now(),
    )
    submit_proposal(p_pending, store)
    try:
        execute_approved_write("GC6-PENDING", fake_write, store)
        results["pending_blocked"] = False
    except WriteBlockedError:
        results["pending_blocked"] = True

    # --- Rejected: direct write attempt must fail ---
    p_rejected = Proposal(
        id="GC6-REJECTED", proposal_type="test", source_ref="Y",
        original_payload={"a": 2}, created_at=datetime.now(),
    )
    submit_proposal(p_rejected, store)
    reject("GC6-REJECTED", approver="eval-harness", store=store)
    try:
        execute_approved_write("GC6-REJECTED", fake_write, store)
        results["rejected_blocked"] = False
    except WriteBlockedError:
        results["rejected_blocked"] = True

    # --- Approved as-is: write must succeed, audit trail correct ---
    p_approved = Proposal(
        id="GC6-APPROVED", proposal_type="test", source_ref="Z",
        original_payload={"a": 3}, created_at=datetime.now(),
    )
    submit_proposal(p_approved, store)
    approve("GC6-APPROVED", approver="lead@example.com", store=store)
    execute_approved_write("GC6-APPROVED", fake_write, store)
    audit_approved = store.get("GC6-APPROVED")
    results["approved_write_succeeded"] = written[-1] == {"a": 3}
    results["approved_audit_correct"] = (
        audit_approved.approver == "lead@example.com"
        and audit_approved.decided_at is not None
        and audit_approved.original_payload == {"a": 3}
        and audit_approved.final_payload == {"a": 3}
    )

    # --- Edit-then-approve: final_payload must differ from original, both retained ---
    p_edited = Proposal(
        id="GC6-EDITED", proposal_type="test", source_ref="W",
        original_payload={"a": 4, "note": "draft"}, created_at=datetime.now(),
    )
    submit_proposal(p_edited, store)
    edit_then_approve("GC6-EDITED", approver="lead@example.com", edited_payload={"a": 4, "note": "edited by lead"}, store=store)
    execute_approved_write("GC6-EDITED", fake_write, store)
    audit_edited = store.get("GC6-EDITED")
    results["edit_write_used_final_not_original"] = written[-1] == {"a": 4, "note": "edited by lead"}
    results["edit_audit_retains_both"] = (
        audit_edited.original_payload == {"a": 4, "note": "draft"}
        and audit_edited.final_payload == {"a": 4, "note": "edited by lead"}
        and audit_edited.approver == "lead@example.com"
    )

    passed = all(results.values())
    detail = "; ".join(f"{k}: {v}" for k, v in results.items())
    return passed, passed, True, detail
