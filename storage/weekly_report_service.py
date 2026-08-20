from datetime import date, datetime

from models.snapshot import Snapshot
from models.weekly_report import WeeklyReportFacts, RankedRisk, ScopeChangeItem
from adapters.risk_log_adapter import RiskLogAdapter
from storage.weekly_report_store import get_latest_weekly_report_facts, save_weekly_report_facts
from storage.brief_facts_service import SPRINT_2_START, SPRINT_2_END, SPRINT_2_NAME

SPRINT_1_START = date(2026, 8, 3)
SPRINT_1_END = date(2026, 8, 14)
SPRINT_1_LABEL = "Sprint 1"

_IMPACT_ORDER = {"High": 0, "Medium": 1, "Low": 2}


def _rank_risks(risks: list[dict]) -> list[RankedRisk]:
    ranked = sorted(risks, key=lambda r: _IMPACT_ORDER.get(r.get("impact", "Low"), 3))
    return [
        RankedRisk(
            id=r["id"], description=r["description"], impact=r["impact"],
            item_id=r.get("item_id"), owner=r.get("owner"),
        )
        for r in ranked
    ]


def extract_weekly_report_facts(snapshot: Snapshot, risk_log: RiskLogAdapter) -> WeeklyReportFacts:
    """Deterministic extraction for the weekly report. 'The week'
    is defined as sprint-start-to-latest-snapshot (Sprint 2 to
    date), NOT a fabricated fixed 7-day window, since our real
    transition data doesn't span a full week yet.

    risk_log is a required parameter (interface type) - callers
    must construct a concrete implementation via
    adapters.adapter_factory, never a default fallback here.
    """
    week_start = SPRINT_2_START
    week_end = snapshot.taken_at.date()
    elapsed_days = max((week_end - week_start).days, 1)  # avoid div-by-zero on day 0

    item_titles = {item.id: item.title for item in snapshot.items}

    done_item_ids = {item.id for item in snapshot.items if item.status == "Done"}
    completed_this_period = []
    for item_id in done_item_ids:
        done_transitions = [
            t for t in snapshot.transitions
            if t.item_id == item_id and t.to_status == "Done"
        ]
        if not done_transitions:
            continue
        latest_done = max(done_transitions, key=lambda t: t.timestamp)
        if week_start <= latest_done.timestamp.date() <= week_end:
            completed_this_period.append(item_id)

    items_completed_count = len(completed_this_period)
    velocity_rate = round(items_completed_count / elapsed_days, 2)

    prior_facts = get_latest_weekly_report_facts()
    if prior_facts:
        prior_period_label = prior_facts["sprint_name"] + f" ({prior_facts['week_start']} to {prior_facts['week_end']})"
        prior_period_days = prior_facts["elapsed_days"]
        prior_period_items_completed = prior_facts["items_completed_count"]
        prior_period_velocity_rate = prior_facts["velocity_rate"]
    else:
        sprint1_done = []
        for item_id in done_item_ids:
            done_transitions = [
                t for t in snapshot.transitions
                if t.item_id == item_id and t.to_status == "Done"
            ]
            if not done_transitions:
                continue
            latest_done = max(done_transitions, key=lambda t: t.timestamp)
            if SPRINT_1_START <= latest_done.timestamp.date() <= SPRINT_1_END:
                sprint1_done.append(item_id)
        sprint1_days = (SPRINT_1_END - SPRINT_1_START).days + 1
        if sprint1_done:
            prior_period_label = SPRINT_1_LABEL
            prior_period_days = sprint1_days
            prior_period_items_completed = len(sprint1_done)
            prior_period_velocity_rate = round(len(sprint1_done) / sprint1_days, 2)
        else:
            prior_period_label = None
            prior_period_days = None
            prior_period_items_completed = None
            prior_period_velocity_rate = None

    scope_added = [
        ScopeChangeItem(item_id=item.id, title=item.title, created_at=item.created_at.isoformat())
        for item in snapshot.items
        if week_start < item.created_at.date() <= SPRINT_2_END
    ]

    risks = risk_log.load_risks()
    top_risks = _rank_risks(risks)
    decisions_needed = [r for r in top_risks if r.owner is None]

    facts = WeeklyReportFacts(
        sprint_name=SPRINT_2_NAME,
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        elapsed_days=elapsed_days,
        items_completed_this_period=completed_this_period,
        items_completed_count=items_completed_count,
        velocity_rate=velocity_rate,
        prior_period_label=prior_period_label,
        prior_period_days=prior_period_days,
        prior_period_items_completed=prior_period_items_completed,
        prior_period_velocity_rate=prior_period_velocity_rate,
        scope_added_mid_sprint=scope_added,
        top_risks=top_risks,
        decisions_needed=decisions_needed,
        item_titles=item_titles,
    )

    save_weekly_report_facts(facts.model_dump())
    return facts
