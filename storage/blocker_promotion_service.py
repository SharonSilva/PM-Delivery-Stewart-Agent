from datetime import datetime

from models.snapshot import Snapshot
from models.proposal import Proposal
from storage.risk_log_store import load_risk_log
from storage.proposal_store import get_all_proposals, save_proposal
from storage.brief_facts_service import _days_blocked
from config.scheduler_config import BLOCKER_PROMOTION_THRESHOLD_DAYS

PROPOSAL_TYPE = "blocker_promotion"


def _already_has_proposal(item_id: str) -> bool:
    """Same dedup pattern as P4: any prior proposal (any status)
    for this item's promotion means don't propose again."""
    existing = get_all_proposals()
    return any(
        p.proposal_type == PROPOSAL_TYPE and p.source_ref == item_id
        for p in existing
    )


def detect_promotion_candidates(
    snapshot: Snapshot,
    threshold_days: int = BLOCKER_PROMOTION_THRESHOLD_DAYS,
) -> list[Proposal]:
    """For each currently-blocked item whose age (from transitions)
    is >= threshold_days, and which hasn't already been proposed
    for promotion, create a draft promotion proposal with mitigation
    wording and the age evidence. threshold_days defaults to config
    but is a real parameter - this is what makes the threshold
    genuinely configuration, not a hardcoded literal, and lets the
    golden case prove that changing it changes the result."""
    risks = load_risk_log()
    risk_item_ids = {r["item_id"] for r in risks if r.get("item_id")}

    as_of = snapshot.taken_at
    new_proposals = []

    for item in snapshot.items:
        if item.status != "Blocked":
            continue

        age_days = _days_blocked(item.id, snapshot.transitions, as_of)
        if age_days < threshold_days:
            continue
        if _already_has_proposal(item.id):
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
        save_proposal(proposal)
        new_proposals.append(proposal)

    return new_proposals
