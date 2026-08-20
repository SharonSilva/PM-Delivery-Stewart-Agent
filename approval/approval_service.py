from datetime import datetime

from models.proposal import Proposal, ProposalStatus
from storage.proposal_store import save_proposal, get_proposal


def submit_proposal(proposal: Proposal) -> None:
    """Any capability wanting to write calls this instead of
    writing directly. The proposal starts PENDING - nothing has
    happened to the real system yet."""
    save_proposal(proposal)


def approve(proposal_id: str, approver: str) -> Proposal:
    """Approve as-is. final_payload = original_payload."""
    proposal = get_proposal(proposal_id)
    if proposal is None:
        raise ValueError(f"No such proposal: {proposal_id}")
    proposal.final_payload = proposal.original_payload
    proposal.status = ProposalStatus.APPROVED
    proposal.decided_at = datetime.now()
    proposal.approver = approver
    save_proposal(proposal)
    return proposal


def edit_then_approve(proposal_id: str, approver: str, edited_payload: dict) -> Proposal:
    """Human modifies the payload before approving. Original stays
    untouched for the audit trail; final_payload reflects the edit."""
    proposal = get_proposal(proposal_id)
    if proposal is None:
        raise ValueError(f"No such proposal: {proposal_id}")
    proposal.final_payload = edited_payload
    proposal.status = ProposalStatus.APPROVED
    proposal.decided_at = datetime.now()
    proposal.approver = approver
    save_proposal(proposal)
    return proposal


def reject(proposal_id: str, approver: str) -> Proposal:
    proposal = get_proposal(proposal_id)
    if proposal is None:
        raise ValueError(f"No such proposal: {proposal_id}")
    proposal.status = ProposalStatus.REJECTED
    proposal.decided_at = datetime.now()
    proposal.approver = approver
    save_proposal(proposal)
    return proposal
