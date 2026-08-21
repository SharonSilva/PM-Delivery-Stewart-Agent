"""
Approval UI - the review-and-approve surface for the delivery lead.
Per the toolkit doc:  Every action here calls the same,
already-tested approval_service/write_gate functions the rest of the
project uses - no new business logic lives in this file.

Run with: streamlit run ui/approval_app.py
"""
import os
import sys
from pathlib import Path

# Streamlit Cloud (and any deployment that runs this file directly,
# not from the project root) does not guarantee the working
# directory is the project root, nor put it on the import path.
# Two things depend on this: importing local packages (adapters/,
# storage/), and every mock adapter's relative seed_data/ path,
# which is resolved at file-open time, not import time. Same root
# cause and fix already proven for mcp_server/server.py.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from adapters.adapter_factory import get_risk_log_adapter, get_proposal_store_adapter
from approval.approval_service import approve, reject, edit_then_approve
from approval.write_gate import execute_approved_write, WriteBlockedError
from storage.risk_log_writer import write_risk_entry, write_promotion_entry

# Same dispatch table as the MCP server - one real write function per
# proposal type that has one. Kept identical on purpose rather than
# duplicated with drift risk; both surfaces call the same underlying
# approval_service/write_gate functions either way.
WRITE_DISPATCH = {
    "risk_gap_fill": write_risk_entry,
    "blocker_promotion": write_promotion_entry,
}

st.set_page_config(page_title="Delivery Steward - Approvals", layout="wide")
st.title("Delivery Steward Pending Approvals")
st.caption("Every write to the risk log goes through this queue. Nothing is written without an explicit decision here.")

store = get_proposal_store_adapter()
all_proposals = store.get_all()
pending = [p for p in all_proposals if p.status.value == "pending"]
decided = [p for p in all_proposals if p.status.value != "pending"]


def handle_approve(proposal_id: str, approver: str):
    write_fn = WRITE_DISPATCH.get(next(p for p in pending if p.id == proposal_id).proposal_type)
    approve(proposal_id, approver=approver, store=store)
    if write_fn is None:
        st.warning(f"Approved, but no write-execution path is wired for this proposal type yet - nothing was written.")
        return
    try:
        execute_approved_write(proposal_id, write_fn, store)
        st.success(f"Approved and executed {proposal_id}.")
    except WriteBlockedError as e:
        st.error(f"Approval recorded but write blocked: {e}")


def handle_reject(proposal_id: str, approver: str):
    reject(proposal_id, approver=approver, store=store)
    st.success(f"Rejected {proposal_id}. No write occurred.")


def handle_edit_then_approve(proposal_id: str, approver: str, edited_payload: dict):
    write_fn = WRITE_DISPATCH.get(next(p for p in pending if p.id == proposal_id).proposal_type)
    edit_then_approve(proposal_id, approver=approver, edited_payload=edited_payload, store=store)
    if write_fn is None:
        st.warning("Approved with edits, but no write-execution path is wired for this proposal type yet.")
        return
    try:
        execute_approved_write(proposal_id, write_fn, store)
        st.success(f"Approved (edited) and executed {proposal_id}.")
    except WriteBlockedError as e:
        st.error(f"Approval recorded but write blocked: {e}")


st.header(f"Pending ({len(pending)})")

if not pending:
    st.info("Nothing pending approval right now.")

approver_name = st.text_input("Your name/identifier (used as the approver on any action below)", value="delivery-lead@example.com")

for p in pending:
    with st.expander(f"{p.id}  —  {p.proposal_type}", expanded=True):
        st.json(p.original_payload)

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(" Approve as-is", key=f"approve_{p.id}"):
                handle_approve(p.id, approver_name)
                st.rerun()
        with col2:
            if st.button(" Reject", key=f"reject_{p.id}"):
                handle_reject(p.id, approver_name)
                st.rerun()
        with col3:
            edit_toggle = st.toggle("Edit before approving", key=f"edit_toggle_{p.id}")

        if edit_toggle:
            edited_json = st.text_area(
                "Edit payload (must remain valid JSON)",
                value=str(p.original_payload).replace("'", '"'),
                key=f"edit_area_{p.id}",
            )
            if st.button("Save edit and approve", key=f"save_edit_{p.id}"):
                import json
                try:
                    edited_payload = json.loads(edited_json)
                    handle_edit_then_approve(p.id, approver_name, edited_payload)
                    st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON: {e}")

st.divider()
st.header(f"Audit trail — decided ({len(decided)})")

if not decided:
    st.caption("No decisions recorded yet.")

for p in sorted(decided, key=lambda x: x.decided_at or "", reverse=True):
    status_icon = "Approved" if p.status.value == "approved" else "Rejected"
    with st.expander(f"{status_icon} {p.id} — {p.status.value} by {p.approver} at {p.decided_at}"):
        st.write("**Original payload:**")
        st.json(p.original_payload)
        if p.final_payload and p.final_payload != p.original_payload:
            st.write("**Final payload (edited before approval):**")
            st.json(p.final_payload)
