from abc import ABC, abstractmethod
from typing import Optional

from models.proposal import Proposal


class ProposalStoreAdapter(ABC):
    """Interface for persisting and retrieving Proposal records.
    Agent logic depends only on this interface, never on a concrete
    implementation - closes a gap where proposal storage was
    previously direct SQLite access with no abstraction layer at
    all, used across P4/P5/P6/P8."""

    @abstractmethod
    def save(self, proposal: Proposal) -> None:
        """Persist a new proposal, or update an existing one
        (matched by id) - e.g. after approve/reject/edit-then-approve."""
        raise NotImplementedError

    @abstractmethod
    def get(self, proposal_id: str) -> Optional[Proposal]:
        """Fetch a single proposal by id, or None if it doesn't exist."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[Proposal]:
        """Return all proposals, oldest first."""
        raise NotImplementedError
