from datetime import datetime

from models.snapshot import Snapshot
from models.proposal import Proposal
from adapters.risk_log_adapter import RiskLogAdapter
from mocks.risk_log_mock import MockRiskLogAdapter
from adapters.proposal_store_adapter import ProposalStoreAdapter
from mocks.proposal_store_sqlite import SqliteProposalStoreAdapter
from storage.brief_facts_service import _days_blocked
from config.scheduler_config import BLOCKER_PROMOTION_THRESHOLD_DAYS

PROPOSAL_TYPE = "blocker_promotion"


def _already_has_proposal(item_id: str, store: ProposalStoreAdapter) -> bool:
    """Same dedup pattern as P4: any prior proposal (any status)
    for this item's promotion means don't propose again."""
    existing = store.get_all()
    return any(
        p.proposal_type == PROPOSAL_TYPE and p.source_ref == item_id
        for p in existing
    )


def detect_promotion_candidates(
    snapshot: Snapshot,
    threshold_days: int = BLOCKER_PROMOTION_THRESHOLD_DAYS,
    risk_log: RiskLogAdapter = None,
    store: ProposalStoreAdapter = None,
) -> list[Proposal]:
    """For each currently-blocked item whose age (from transitions)
    is >= threshold_days, and which hasn't already been proposed
    for promotion, create a draft promotion proposal with mitigation
    wording and the age evidence. threshold_days defaults to config
    but is a real parameter - this is what makes the threshold
    genuinely configuration, not a hardcoded literal.

    risk_log is accepted as a parameter (interface type), defaulting
    to the mock - lets a real integration be swapped in without
    touching this function."""
    if risk_log is None:
        risk_log = MockRiskLogAdapter()
    if store is None:
        store = SqliteProposalStoreAdapter()

    risks = risk_log.load_risks()
    risk_item_ids = {r["item_id"] for r in risks if r.get("item_id")}

    as_of = snapshot.taken_at
    new_proposals = []

    for item in snapshot.items:
        if item.status != "Blocked":
            continue

        age_days = _days_blocked(item.id, snapshot.transitions, as_of)
        if age_days < threshold_days:
            continue
        if _already_has_proposal(item.id, store):
            continue

        already_a_risk = item.id in risk_item_ids

        payload = {
            "item_id": item.id,
            "title": item.title,
            "days_blocked": age_days,
            "already_in_risk_log": already_a_risk,
            "mitigation_draft": (
                f"{item.title} ({item.id}) has been blocked for {age_days} days, "
                f"exceeding the {threshold_days}-day promotion threshold. "
                f"Recommend escalating to an active risk with an owner and a mitigation plan."
            ),
        }

        proposal = Proposal(
            id=f"PROMOTE-{item.id}",
            proposal_type=PROPOSAL_TYPE,
            source_ref=item.id,
            original_payload=payload,
            created_at=datetime.now(),
        )
        store.save(proposal)
        new_proposals.append(proposal)

    return new_proposals
