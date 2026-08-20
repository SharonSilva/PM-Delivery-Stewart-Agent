from datetime import datetime

from models.proposal import Proposal, ProposalStatus
from adapters.proposal_store_adapter import ProposalStoreAdapter
from mocks.proposal_store_sqlite import SqliteProposalStoreAdapter


def _default_store() -> ProposalStoreAdapter:
    return SqliteProposalStoreAdapter()


def submit_proposal(proposal: Proposal, store: ProposalStoreAdapter = None) -> None:
    """Any capability wanting to write calls this instead of
    writing directly. The proposal starts PENDING - nothing has
    happened to the real system yet."""
    if store is None:
        store = _default_store()
    store.save(proposal)


def approve(proposal_id: str, approver: str, store: ProposalStoreAdapter = None) -> Proposal:
    """Approve as-is. final_payload = original_payload."""
    if store is None:
        store = _default_store()
    proposal = store.get(proposal_id)
    if proposal is None:
        raise ValueError(f"No such proposal: {proposal_id}")
    proposal.final_payload = proposal.original_payload
    proposal.status = ProposalStatus.APPROVED
    proposal.decided_at = datetime.now()
    proposal.approver = approver
    store.save(proposal)
    return proposal


def edit_then_approve(proposal_id: str, approver: str, edited_payload: dict, store: ProposalStoreAdapter = None) -> Proposal:
    """Human modifies the payload before approving. Original stays
    untouched for the audit trail; final_payload reflects the edit."""
    if store is None:
        store = _default_store()
    proposal = store.get(proposal_id)
    if proposal is None:
        raise ValueError(f"No such proposal: {proposal_id}")
    proposal.final_payload = edited_payload
    proposal.status = ProposalStatus.APPROVED
    proposal.decided_at = datetime.now()
    proposal.approver = approver
    store.save(proposal)
    return proposal


def reject(proposal_id: str, approver: str, store: ProposalStoreAdapter = None) -> Proposal:
    if store is None:
        store = _default_store()
    proposal = store.get(proposal_id)
    if proposal is None:
        raise ValueError(f"No such proposal: {proposal_id}")
    proposal.status = ProposalStatus.REJECTED
    proposal.decided_at = datetime.now()
    proposal.approver = approver
    store.save(proposal)
    return proposal
