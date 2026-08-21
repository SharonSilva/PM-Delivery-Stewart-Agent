"""
Delivery Steward - the surface a delivery lead actually uses day to
day. Every tab calls existing, already-tested functions from the
rest of the project - no new business logic lives in this file.

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
# which is resolved at file-open time, not import time.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime

import streamlit as st

from adapters.adapter_factory import (
    get_tracker_adapter, get_codehost_adapter, get_chat_adapter,
    get_risk_log_adapter, get_proposal_store_adapter, get_notification_adapter,
)
from storage.snapshot_service import take_snapshot
from storage.brief_facts_service import extract_brief_facts
from storage.morning_brief_service import generate_morning_brief
from storage.eod_delta_service import compute_eod_delta
from storage.eod_summary_service import generate_eod_summary
from storage.risk_gap_service import detect_risk_gaps
from storage.blocker_promotion_service import detect_promotion_candidates
from storage.commitment_tracking_service import run_commitment_check
from storage.meeting_outcome_consumer import process_meeting_outcome
from storage.weekly_report_service import extract_weekly_report_facts
from storage.weekly_report_assembly_service import generate_weekly_report
from storage.sprint_planning_service import extract_sprint_planning_facts
from storage.sprint_planning_assembly_service import generate_sprint_planning_pack
from storage.delivery_narrative_service import extract_delivery_narrative_facts
from storage.delivery_narrative_assembly_service import generate_delivery_narrative
from approval.approval_service import approve, reject, edit_then_approve
from approval.write_gate import execute_approved_write, WriteBlockedError
from storage.risk_log_writer import write_risk_entry, write_promotion_entry
from scheduler.clock import clock

WRITE_DISPATCH = {
    "risk_gap_fill": write_risk_entry,
    "blocker_promotion": write_promotion_entry,
}

st.set_page_config(page_title="Delivery Steward", layout="wide")
st.title("Delivery Steward")
st.caption("What a delivery lead sees each day: the morning brief, the end-of-day summary, and the approval queue for anything the agent wants to write.")

(tab_morning, tab_eod, tab_promotion, tab_commitments, tab_meetings,
 tab_weekly, tab_sprint, tab_narrative, tab_approvals) = st.tabs([
    "Morning Brief", "End of Day", "Blocker Promotion", "Commitments",
    "Meeting Outcomes", "Weekly Report", "Sprint Planning", "Delivery Narrative", "Approvals",
])

store = get_proposal_store_adapter()

# ---------- Morning Brief tab ----------
with tab_morning:
    st.header("Morning Brief")
    demo_date = st.date_input("Date to generate the brief for (seed data covers Aug 2026)", value=datetime(2026, 8, 18).date())
    if st.button("Generate morning brief", key="gen_morning"):
        with st.spinner("Generating brief - this calls a local LLM and can take up to a minute..."):
            clock.set_override(datetime(demo_date.year, demo_date.month, demo_date.day, 9, 0, 0))
            tracker = get_tracker_adapter()
            codehost = get_codehost_adapter()
            chat = get_chat_adapter()
            risk_log = get_risk_log_adapter()
            snapshot = take_snapshot(tracker, codehost, chat, as_of=clock.now())
            facts = extract_brief_facts(snapshot, risk_log)
            brief = generate_morning_brief(facts)
            rendered = brief.render()
            gap_proposals = detect_risk_gaps(snapshot, risk_log, store)
        st.code(rendered, language=None)
        if gap_proposals:
            st.warning(f"{len(gap_proposals)} new risk-gap proposal(s) created - see the Approvals tab.")
            for p in gap_proposals:
                st.write(f"- **{p.id}**: {p.original_payload['description']}")
        else:
            st.info("No new risk gaps found.")

# ---------- End of Day tab ----------
with tab_eod:
    st.header("End of Day Summary")
    demo_date_eod = st.date_input("Date to generate the EOD summary for (seed data covers Aug 2026)", value=datetime(2026, 8, 18).date(), key="eod_date")
    if st.button("Generate EOD summary", key="gen_eod"):
        with st.spinner("Generating EOD summary - this calls a local LLM and can take up to a minute..."):
            clock.set_override(datetime(demo_date_eod.year, demo_date_eod.month, demo_date_eod.day, 18, 0, 0))
            tracker = get_tracker_adapter()
            codehost = get_codehost_adapter()
            chat = get_chat_adapter()
            morning_snapshot = take_snapshot(tracker, codehost, chat, as_of=datetime(demo_date_eod.year, demo_date_eod.month, demo_date_eod.day, 9, 0, 0))
            eod_snapshot = take_snapshot(tracker, codehost, chat, as_of=clock.now())
            delta = compute_eod_delta(morning_snapshot, eod_snapshot)
            summary = generate_eod_summary(delta)
            rendered = summary.render()
        st.code(rendered, language=None)

# ---------- Blocker Promotion tab ----------
with tab_promotion:
    st.header("Blocker-to-Risk Promotion")
    demo_date_promo = st.date_input("Date to check for stale blockers", value=datetime(2026, 8, 18).date(), key="promo_date")
    threshold = st.number_input("Promotion threshold (days blocked)", min_value=1, value=2, key="promo_threshold")
    if st.button("Check for promotion candidates", key="gen_promo"):
        with st.spinner("Checking blockers..."):
            clock.set_override(datetime(demo_date_promo.year, demo_date_promo.month, demo_date_promo.day, 18, 0, 0))
            tracker = get_tracker_adapter()
            codehost = get_codehost_adapter()
            chat = get_chat_adapter()
            risk_log = get_risk_log_adapter()
            snapshot = take_snapshot(tracker, codehost, chat, as_of=clock.now())
            promo_proposals = detect_promotion_candidates(snapshot, risk_log, store, threshold_days=threshold)
        if promo_proposals:
            st.warning(f"{len(promo_proposals)} new promotion proposal(s) - see the Approvals tab.")
            for p in promo_proposals:
                st.write(f"- **{p.id}**: {p.original_payload['mitigation_draft']}")
        else:
            st.info("No blockers exceed the configured threshold.")

# ---------- Commitments tab ----------
with tab_commitments:
    st.header("Commitment Tracking")
    demo_date_commit = st.date_input("Date to run the commitment check for", value=datetime(2026, 8, 18).date(), key="commit_date")
    if st.button("Run commitment check", key="gen_commit"):
        with st.spinner("Checking commitments..."):
            notification_adapter = get_notification_adapter()
            result = run_commitment_check(as_of_date=demo_date_commit, notification_adapter=notification_adapter)
        st.write(f"**{len(result['nudges_sent'])} nudge(s) sent, {len(result['escalations'])} escalation(s), {len(result['capped_skips'])} capped.**")
        for entry in result["ageing_view"]:
            st.write(f"- {entry['id']} ({entry['person']}): {entry['classification']}")

# ---------- Meeting Outcomes tab ----------
with tab_meetings:
    st.header("Meeting Outcome Consumption")
    st.caption("Processes the seeded meeting-outcome records (seed_data/meeting_outcomes.json).")
    if st.button("Process meeting outcomes", key="gen_meetings"):
        import json
        with open("seed_data/meeting_outcomes.json") as f:
            outcomes = json.load(f)["meeting_outcomes"]
        for record in outcomes:
            result = process_meeting_outcome(record, store)
            if result.refused:
                st.error(f"{record['id']}: REFUSED - {result.reason}")
            else:
                st.success(f"{record['id']}: processed - {len(result.tracker_proposals)} tracker + {len(result.risk_proposals)} risk proposal(s) created (see Approvals tab).")

# ---------- Weekly Report tab ----------
with tab_weekly:
    st.header("Weekly Status Report")
    demo_date_weekly = st.date_input("Date to generate the weekly report for", value=datetime(2026, 8, 18).date(), key="weekly_date")
    if st.button("Generate weekly report", key="gen_weekly"):
        with st.spinner("Generating weekly report - this calls a local LLM..."):
            clock.set_override(datetime(demo_date_weekly.year, demo_date_weekly.month, demo_date_weekly.day, 18, 0, 0))
            tracker = get_tracker_adapter()
            codehost = get_codehost_adapter()
            chat = get_chat_adapter()
            risk_log = get_risk_log_adapter()
            snapshot = take_snapshot(tracker, codehost, chat, as_of=clock.now())
            facts = extract_weekly_report_facts(snapshot, risk_log)
            report = generate_weekly_report(facts)
            rendered = report.render()
        st.code(rendered, language=None)

# ---------- Sprint Planning tab ----------
with tab_sprint:
    st.header("Sprint Planning Pack")
    demo_date_sprint = st.date_input("Date to generate the planning pack for", value=datetime(2026, 8, 18).date(), key="sprint_date")
    if st.button("Generate sprint planning pack", key="gen_sprint"):
        with st.spinner("Generating sprint planning pack..."):
            clock.set_override(datetime(demo_date_sprint.year, demo_date_sprint.month, demo_date_sprint.day, 18, 0, 0))
            tracker = get_tracker_adapter()
            codehost = get_codehost_adapter()
            chat = get_chat_adapter()
            snapshot = take_snapshot(tracker, codehost, chat, as_of=clock.now())
            facts = extract_sprint_planning_facts(snapshot)
            pack = generate_sprint_planning_pack(facts)
            rendered = pack.render()
        st.code(rendered, language=None)

# ---------- Delivery Narrative tab ----------
with tab_narrative:
    st.header("Delivery Narrative")
    demo_date_narrative = st.date_input("Date to generate the narrative for", value=datetime(2026, 8, 18).date(), key="narrative_date")
    if st.button("Generate delivery narrative", key="gen_narrative"):
        with st.spinner("Generating delivery narrative - this calls a local LLM..."):
            clock.set_override(datetime(demo_date_narrative.year, demo_date_narrative.month, demo_date_narrative.day, 18, 0, 0))
            tracker = get_tracker_adapter()
            codehost = get_codehost_adapter()
            chat = get_chat_adapter()
            risk_log = get_risk_log_adapter()
            snapshot = take_snapshot(tracker, codehost, chat, as_of=clock.now())
            facts = extract_delivery_narrative_facts(snapshot, risk_log)
            narrative = generate_delivery_narrative(facts)
            rendered = narrative.render()
        st.code(rendered, language=None)

# ---------- Approvals tab ----------
with tab_approvals:
    st.header("Pending Approvals")
    st.caption("Every write to the risk log goes through this queue. Nothing is written without an explicit decision here.")

    all_proposals = store.get_all()
    pending = [p for p in all_proposals if p.status.value == "pending"]
    decided = [p for p in all_proposals if p.status.value != "pending"]

    def handle_approve(proposal_id: str, approver: str):
        write_fn = WRITE_DISPATCH.get(next(p for p in pending if p.id == proposal_id).proposal_type)
        approve(proposal_id, approver=approver, store=store)
        if write_fn is None:
            st.warning("Approved, but no write-execution path is wired for this proposal type yet - nothing was written.")
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

    st.subheader(f"Pending ({len(pending)})")

    if not pending:
        st.info("Nothing pending approval right now. Generate a morning brief to create some.")

    approver_name = st.text_input("Your name/identifier (used as the approver on any action below)", value="delivery-lead@example.com")

    for p in pending:
        with st.expander(f"{p.id}  —  {p.proposal_type}", expanded=True):
            st.json(p.original_payload)

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Approve as-is", key=f"approve_{p.id}"):
                    handle_approve(p.id, approver_name)
                    st.rerun()
            with col2:
                if st.button("Reject", key=f"reject_{p.id}"):
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
    st.subheader(f"Audit trail — decided ({len(decided)})")

    if not decided:
        st.caption("No decisions recorded yet.")

    for p in sorted(decided, key=lambda x: x.decided_at or "", reverse=True):
        status_label = "Approved" if p.status.value == "approved" else "Rejected"
        with st.expander(f"{status_label} — {p.id} by {p.approver} at {p.decided_at}"):
            st.write("**Original payload:**")
            st.json(p.original_payload)
            if p.final_payload and p.final_payload != p.original_payload:
                st.write("**Final payload (edited before approval):**")
                st.json(p.final_payload)
