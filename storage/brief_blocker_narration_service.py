from models.brief_facts import BlockerFact
from models.brief_output import NarratedBrief, BriefLine


def narrate_blocker(blocker: BlockerFact) -> NarratedBrief:
    """Blockers are narrated directly from facts, no LLM needed 
    the fact set is small and precise enough that generation adds
    risk without benefit here."""
    risk_note = "" if blocker.in_risk_log else " (not yet in the risk log)"
    text = (
        f"{blocker.item_id} (\"{blocker.title}\") has been blocked for "
        f"{blocker.days_blocked} day{'s' if blocker.days_blocked != 1 else ''}"
        f"{', assigned to ' + blocker.assignee if blocker.assignee else ', unassigned'}"
        f"{risk_note}."
    )
    return NarratedBrief(lines=[BriefLine(text=text, source_ref=blocker.item_id)])
