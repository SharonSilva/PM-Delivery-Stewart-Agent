from approval.approval_service import approve
from approval.write_gate import execute_approved_write
from storage.risk_log_writer import write_promotion_entry


def approve_and_write_promotion(proposal_id: str, approver: str) -> None:
    approve(proposal_id, approver)
    execute_approved_write(proposal_id, write_promotion_entry)
