from datetime import datetime

from models.proposal import Proposal, ProposalStatus
from adapters.proposal_store_adapter import ProposalStoreAdapter


def submit_proposal(proposal: Proposal, store: ProposalStoreAdapter) -> None:
    """Any capability wanting to write calls this instead of
    writing directly. The proposal starts PENDING - nothing has
    happened to the real system yet.

    store is a required parameter (interface type) - callers must
    construct a concrete implementation via adapters.adapter_factory,
    never a default fallback here."""
    store.save(proposal)


def approve(proposal_id: str, approver: str, store: ProposalStoreAdapter) -> Proposal:
    """Approve as-is. final_payload = original_payload."""
    proposal = store.get(proposal_id)
    if proposal is None:
        raise ValueError(f"No such proposal: {proposal_id}")
    proposal.final_payload = proposal.original_payload
    proposal.status = ProposalStatus.APPROVED
    proposal.decided_at = datetime.now()
    proposal.approver = approver
    store.save(proposal)
    return proposal


def edit_then_approve(proposal_id: str, approver: str, edited_payload: dict, store: ProposalStoreAdapter) -> Proposal:
    """Human modifies the payload before approving. Original stays
    untouched for the audit trail; final_payload reflects the edit."""
    proposal = store.get(proposal_id)
    if proposal is None:
        raise ValueError(f"No such proposal: {proposal_id}")
    proposal.final_payload = edited_payload
    proposal.status = ProposalStatus.APPROVED
    proposal.decided_at = datetime.now()
    proposal.approver = approver
    store.save(proposal)
    return proposal


def reject(proposal_id: str, approver: str, store: ProposalStoreAdapter) -> Proposal:
    proposal = store.get(proposal_id)
    if proposal is None:
        raise ValueError(f"No such proposal: {proposal_id}")
    proposal.status = ProposalStatus.REJECTED
    proposal.decided_at = datetime.now()
    proposal.approver = approver
    store.save(proposal)
    return proposal
