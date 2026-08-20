from datetime import datetime

from models.snapshot import Snapshot
from models.proposal import Proposal, ProposalStatus
from adapters.risk_log_adapter import RiskLogAdapter
from mocks.risk_log_mock import MockRiskLogAdapter
from storage.proposal_store import get_all_proposals, save_proposal

PROPOSAL_TYPE = "risk_gap_fill"


def _blocker_facts(snapshot: Snapshot) -> list[dict]:
    """Every currently-blocked item, with enough info to draft a
    risk entry: id, title, assignee (owner, only if evidenced)."""
    return [
        {"item_id": item.id, "title": item.title, "assignee": item.assignee}
        for item in snapshot.items
        if item.status == "Blocked"
    ]


def _already_has_proposal(item_id: str) -> bool:
    """True if ANY proposal (pending, approved, or rejected) already
    exists for this blocker's gap-fill. This is what prevents
    re-proposing an identical entry after rejection - the check is
    on prior proposals, not just the current risk log state."""
    existing = get_all_proposals()
    return any(
        p.proposal_type == PROPOSAL_TYPE and p.source_ref == item_id
        for p in existing
    )


def detect_risk_gaps(snapshot: Snapshot, risk_log: RiskLogAdapter = None) -> list[Proposal]:
    """For each blocker not in the risk log AND not already
    proposed before (in any status), create a new pending proposal
    with a draft risk entry. Returns the list of newly-created
    proposals (not proposals that already existed).

    risk_log is accepted as a parameter (interface type), defaulting
    to the mock - this is what lets a real integration be swapped in
    later without touching this function, and what a central
    adapter factory will supply going forward."""
    if risk_log is None:
        risk_log = MockRiskLogAdapter()

    risks = risk_log.load_risks()
    risk_item_ids = {r["item_id"] for r in risks if r.get("item_id")}

    new_proposals = []
    for blocker in _blocker_facts(snapshot):
        item_id = blocker["item_id"]

        if item_id in risk_item_ids:
            continue  # already has a real risk entry
        if _already_has_proposal(item_id):
            continue  # already proposed before (any status) - don't duplicate

        payload = {
            "description": f"{blocker['title']} ({item_id}) is currently blocked and has no corresponding risk-log entry.",
            "impact": "Medium",  # conservative default; human can edit on approval
            "suggested_owner": blocker["assignee"] if blocker["assignee"] else None,
            "item_id": item_id,
        }

        proposal = Proposal(
            id=f"RISK-GAP-{item_id}",
            proposal_type=PROPOSAL_TYPE,
            source_ref=item_id,
            original_payload=payload,
            created_at=datetime.now(),
        )
        save_proposal(proposal)
        new_proposals.append(proposal)

    return new_proposals
