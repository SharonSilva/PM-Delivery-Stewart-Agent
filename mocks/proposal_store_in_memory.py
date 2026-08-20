from typing import Optional

from adapters.proposal_store_adapter import ProposalStoreAdapter
from models.proposal import Proposal


class InMemoryProposalStoreAdapter(ProposalStoreAdapter):
    """A second, deliberately different implementation of
    ProposalStoreAdapter - NOT SQLite, just proof the interface
    can be satisfied by something else entirely. Concrete swap-test
    proof: agent logic (execute_approved_write, approval_service)
    never changes, only the factory's returned instance does."""

    def __init__(self):
        self._proposals: dict[str, Proposal] = {}

    def save(self, proposal: Proposal) -> None:
        self._proposals[proposal.id] = proposal

    def get(self, proposal_id: str) -> Optional[Proposal]:
        return self._proposals.get(proposal_id)

    def get_all(self) -> list[Proposal]:
        return sorted(self._proposals.values(), key=lambda p: p.created_at)
