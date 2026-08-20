from approval.approval_service import approve
from approval.write_gate import execute_approved_write
from storage.risk_log_writer import write_risk_entry


def approve_and_write_risk_gap(proposal_id: str, approver: str) -> None:
    """Approves a risk-gap-fill proposal AND writes it to the risk
    log in one call - convenience wrapper, but the underlying
    write_gate still enforces that this can never succeed unless
    the approval genuinely happened first."""
    approve(proposal_id, approver)
    execute_approved_write(proposal_id, write_risk_entry)
