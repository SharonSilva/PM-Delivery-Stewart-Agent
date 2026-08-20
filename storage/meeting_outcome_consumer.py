from datetime import datetime

from models.proposal import Proposal
from adapters.proposal_store_adapter import ProposalStoreAdapter
from mocks.proposal_store_sqlite import SqliteProposalStoreAdapter
from storage.refusal_log import log_refusal

TRACKER_PROPOSAL_TYPE = "meeting_tracker_update"
RISK_PROPOSAL_TYPE = "meeting_risk_entry"


class MeetingOutcomeResult:
    def __init__(self, refused: bool, reason: str = None, tracker_proposals=None, risk_proposals=None):
        self.refused = refused
        self.reason = reason
        self.tracker_proposals = tracker_proposals or []
        self.risk_proposals = risk_proposals or []


def process_meeting_outcome(record: dict, store: ProposalStoreAdapter = None) -> MeetingOutcomeResult:
    """Consumes one meeting-outcome record. If consent is not
    exactly True, refuses OUTRIGHT - no proposal is created, the
    refusal is logged with a reason. This is a pre-proposal gate,
    distinct from the approval gate: a refused record never even
    reaches the point of being something a human could approve."""

    if store is None:
        store = SqliteProposalStoreAdapter()

    meeting_id = record["id"]
    consent = record.get("consent")

    if consent is not True:
        reason = f"consent flag is {consent!r}, not True - record refused before processing"
        log_refusal(meeting_id, reason)
        return MeetingOutcomeResult(refused=True, reason=reason)

    tracker_proposals = []
    for i, decision in enumerate(record.get("decisions", [])):
        payload = {
            "meeting_id": meeting_id,
            "kind": "decision",
            "text": decision["text"],
            "related_item": decision.get("source_ref"),
        }
        proposal = Proposal(
            id=f"MTG-{meeting_id}-DECISION-{i}",
            proposal_type=TRACKER_PROPOSAL_TYPE,
            source_ref=meeting_id,
            original_payload=payload,
            created_at=datetime.now(),
        )
        store.save(proposal)
        tracker_proposals.append(proposal)

    for i, action in enumerate(record.get("actions", [])):
        payload = {
            "meeting_id": meeting_id,
            "kind": "action",
            "text": action["text"],
            "person": action.get("person"),
            "due_date": action.get("due_date"),
            "related_item": action.get("source_ref"),
        }
        proposal = Proposal(
            id=f"MTG-{meeting_id}-ACTION-{i}",
            proposal_type=TRACKER_PROPOSAL_TYPE,
            source_ref=meeting_id,
            original_payload=payload,
            created_at=datetime.now(),
        )
        store.save(proposal)
        tracker_proposals.append(proposal)

    risk_proposals = []
    for i, risk in enumerate(record.get("risks", [])):
        payload = {
            "meeting_id": meeting_id,
            "text": risk["text"],
            "related_item": risk.get("source_ref"),
        }
        proposal = Proposal(
            id=f"MTG-{meeting_id}-RISK-{i}",
            proposal_type=RISK_PROPOSAL_TYPE,
            source_ref=meeting_id,
            original_payload=payload,
            created_at=datetime.now(),
        )
        store.save(proposal)
        risk_proposals.append(proposal)

    return MeetingOutcomeResult(
        refused=False,
        tracker_proposals=tracker_proposals,
        risk_proposals=risk_proposals,
    )
