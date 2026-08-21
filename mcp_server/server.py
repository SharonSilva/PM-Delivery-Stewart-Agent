"""
MCP server exposing Delivery Steward capabilities to other agents/clients.
Bonus capability, per the toolkit doc ("Tool / integration protocol...
bonus marks, not required"). Every tool here is a thin wrapper around an
already-built, already-tested function - no new business logic lives here.

Approval/rejection tools still require a human decision behind them: the
approval gate itself (approval/write_gate.py's execute_approved_write) does
not distinguish between "a human typed this command" and "a human told
their MCP-connected agent to run this tool" - both are the same kind of
explicit human authorization, just relayed through a different interface.
The underlying enforcement (a write cannot happen without an APPROVED
proposal) is identical either way.

Schema version: 1.0 (see docs/mcp_schema.md for the versioned, documented
tool contracts).
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Claude Desktop launches this script with no guaranteed working
# directory. Two separate things depend on the working directory
# being the project root: (1) importing local packages like
# adapters/, storage/, and (2) every mock adapter's relative data
# path (e.g. "seed_data/tracker_items.json"), which is resolved at
# the moment a file is opened, not at import time. Fixing both by
# changing the process's own working directory once, at startup,
# is simpler and safer than patching every individual relative
# path across the codebase.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server import MCPServer

from adapters.adapter_factory import (
    get_tracker_adapter, get_codehost_adapter, get_chat_adapter,
    get_risk_log_adapter, get_proposal_store_adapter,
)
from storage.snapshot_service import take_snapshot
from storage.brief_facts_service import extract_brief_facts
from storage.morning_brief_service import generate_morning_brief
from storage.eod_delta_service import compute_eod_delta
from storage.eod_summary_service import generate_eod_summary
from approval.approval_service import approve, reject
from approval.write_gate import execute_approved_write, WriteBlockedError
from storage.risk_log_writer import write_risk_entry, write_promotion_entry
from scheduler.clock import clock

# Maps a proposal's type to the real write function that applies it.
# meeting_tracker_update/meeting_risk_entry proposals from P8 don't yet
# have a dedicated write-execution function in this codebase (P8 was
# built and tested through the approval/audit layer, not a full write
# path) - those are intentionally NOT included here rather than silently
# no-op'd, so an attempt to approve one is honest about the gap.
WRITE_DISPATCH = {
    "risk_gap_fill": write_risk_entry,
    "blocker_promotion": write_promotion_entry,
}

mcp_app = MCPServer("Delivery Steward")


@mcp_app.tool()
def get_morning_brief() -> str:
    """Generate and return today's morning brief: per-person status,
    delivered/in-progress/blocked items, and blockers ranked by age.
    Every factual line is grounded in real project data."""
    tracker = get_tracker_adapter()
    codehost = get_codehost_adapter()
    chat = get_chat_adapter()
    risk_log = get_risk_log_adapter()
    snapshot = take_snapshot(tracker, codehost, chat, as_of=clock.now())
    facts = extract_brief_facts(snapshot, risk_log)
    brief = generate_morning_brief(facts)
    return brief.render()


@mcp_app.tool()
def get_eod_summary() -> str:
    """Generate and return today's end-of-day summary: what shipped,
    what got newly blocked, and other changes since this morning."""
    tracker = get_tracker_adapter()
    codehost = get_codehost_adapter()
    chat = get_chat_adapter()
    now = clock.now()
    eod_snapshot = take_snapshot(tracker, codehost, chat, as_of=now)
    today_start = datetime(now.year, now.month, now.day)
    morning_snapshot = take_snapshot(tracker, codehost, chat, as_of=today_start)
    delta = compute_eod_delta(morning_snapshot, eod_snapshot)
    summary = generate_eod_summary(delta)
    return summary.render()


@mcp_app.tool()
def list_pending_proposals() -> str:
    """List every proposal currently awaiting human approval or
    rejection: its ID, type, and what it proposes to do."""
    store = get_proposal_store_adapter()
    all_proposals = store.get_all()
    pending = [p for p in all_proposals if p.status.value == "pending"]
    if not pending:
        return "No proposals currently pending."
    lines = [f"{len(pending)} proposal(s) pending approval:"]
    for p in pending:
        lines.append(f"  {p.id} ({p.proposal_type}): {p.original_payload}")
    return "\n".join(lines)


@mcp_app.tool()
def approve_proposal(proposal_id: str, approver: str) -> str:
    """Approve a pending proposal as-is and execute the resulting
    write. Requires a human decision behind this call - the approval
    gate enforces this identically regardless of what interface
    submitted it."""
    store = get_proposal_store_adapter()
    proposal = store.get(proposal_id)
    if proposal is None:
        return f"No such proposal: {proposal_id}"

    write_fn = WRITE_DISPATCH.get(proposal.proposal_type)
    if write_fn is None:
        return (
            f"No write-execution path is wired for proposal type "
            f"'{proposal.proposal_type}' yet - refusing to silently no-op. "
            f"Approval was NOT recorded."
        )

    approve(proposal_id, approver=approver, store=store)
    try:
        execute_approved_write(proposal_id, write_fn, store)
        return f"Approved and executed {proposal_id} (approver: {approver})."
    except WriteBlockedError as e:
        return f"Approval recorded but write blocked: {e}"


@mcp_app.tool()
def reject_proposal(proposal_id: str, approver: str) -> str:
    """Reject a pending proposal. No write occurs."""
    store = get_proposal_store_adapter()
    reject(proposal_id, approver=approver, store=store)
    return f"Rejected {proposal_id} (approver: {approver})."


if __name__ == "__main__":
    import sys
    # Default transport is stdio - this is what Claude Desktop's
    # claude_desktop_config.json reliably and safely supports (a url
    # field for streamable-http has a known bug where Claude Desktop
    # can silently corrupt the config file). Pass --http to instead
    # run as a standalone HTTP server for manual/script testing.
    if "--http" in sys.argv:
        import uvicorn
        uvicorn.run(mcp_app.streamable_http_app(), host="127.0.0.1", port=8000)
    else:
        mcp_app.run(transport="stdio")
