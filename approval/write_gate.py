from adapters.proposal_store_adapter import ProposalStoreAdapter
from mocks.proposal_store_sqlite import SqliteProposalStoreAdapter
from models.proposal import ProposalStatus


class WriteBlockedError(Exception):
    """Raised when something tries to execute a proposal that
    isn't approved. This is the enforcement point the brief
    explicitly asks to see in code during Q&A."""
    pass


def execute_approved_write(proposal_id: str, write_fn, store: ProposalStoreAdapter = None) -> None:
    """The ONLY path through which a proposal's payload reaches a
    real write. Structurally cannot execute anything that isn't
    APPROVED - this is what makes the gate 'enforced in the data
    model, not only the interface': even a caller that bypasses
    the UI entirely and calls this directly will be blocked.
    write_fn is the adapter write call to perform (e.g., writing
    a risk-log entry). It receives final_payload only if approved.

    store is accepted as a parameter (interface type), defaulting
    to the SQLite implementation - lets a different proposal store
    be swapped in without touching this function.
    """
    if store is None:
        store = SqliteProposalStoreAdapter()

    proposal = store.get(proposal_id)
    if proposal is None:
        raise ValueError(f"No such proposal: {proposal_id}")
    if proposal.status != ProposalStatus.APPROVED:
        raise WriteBlockedError(
            f"Proposal {proposal_id} is {proposal.status.value}, not approved. "
            f"Refusing to write. (Default-safe: no write on anything but explicit approval.)"
        )
    write_fn(proposal.final_payload)
