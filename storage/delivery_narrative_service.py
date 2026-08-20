from datetime import date, datetime
from typing import Optional

from models.snapshot import Snapshot
from models.delivery_narrative import BlockerPeriod, ScopeEvent, TemporalAssociation, DeliveryNarrativeFacts
from storage.weekly_report_service import extract_weekly_report_facts
from storage.weekly_narration_service import _classify_velocity_change


def _compute_blocker_periods(snapshot: Snapshot, period_start: date, period_end: date) -> list[BlockerPeriod]:
    item_titles = {item.id: item.title for item in snapshot.items}
    by_item: dict[str, list] = {}
    for t in snapshot.transitions:
        by_item.setdefault(t.item_id, []).append(t)

    periods = []
    for item_id, transitions in by_item.items():
        transitions.sort(key=lambda t: t.timestamp)
        blocked_start = None
        for t in transitions:
            if t.to_status == "Blocked" and blocked_start is None:
                blocked_start = t.timestamp
            elif t.from_status == "Blocked" and blocked_start is not None:
                end = t.timestamp
                if blocked_start.date() <= period_end and end.date() >= period_start:
                    periods.append(BlockerPeriod(
                        item_id=item_id,
                        title=item_titles.get(item_id, "(unknown)"),
                        blocked_from=blocked_start.isoformat(),
                        blocked_until=end.isoformat(),
                        days_blocked=(end - blocked_start).days,
                    ))
                blocked_start = None
        if blocked_start is not None and blocked_start.date() <= period_end:
            days = (datetime.combine(period_end, datetime.max.time()) - blocked_start).days
            periods.append(BlockerPeriod(
                item_id=item_id,
                title=item_titles.get(item_id, "(unknown)"),
                blocked_from=blocked_start.isoformat(),
                blocked_until=None,
                days_blocked=days,
            ))
    return periods


def _compute_scope_events(snapshot: Snapshot, period_start: date, period_end: date) -> list[ScopeEvent]:
    item_titles = {item.id: item.title for item in snapshot.items}
    events = []
    for item in snapshot.items:
        created = item.created_at.date()
        if period_start <= created <= period_end:
            events.append(ScopeEvent(item_id=item.id, title=item_titles[item.id], event_date=created.isoformat()))
    return events


def _compute_associations(
    blocker_periods: list[BlockerPeriod], scope_events: list[ScopeEvent], velocity_direction: Optional[str]
) -> list[TemporalAssociation]:
    """Pure code temporal join. Builds cited_item_ids and the
    description text from the SAME underlying event list, in the
    same order, so the citations always match what's actually
    described - fixes a real bug where an earlier version built
    the two from differently-deduplicated collections and they
    silently diverged."""
    associations = []
    if velocity_direction not in ("increased", "decreased"):
        return associations

    all_events = [(b.item_id, "blocked") for b in blocker_periods] + [(s.item_id, "scope-added") for s in scope_events]

    # Require at least 2 DISTINCT items, not just 2 events - a
    # single item appearing as both a blocker and a scope-add
    # should not count as satisfying the citation requirement,
    # since that reads as padding rather than genuine breadth of
    # evidence.
    distinct_items_seen = []
    selected_events = []
    for eid, kind in all_events:
        if eid not in distinct_items_seen:
            distinct_items_seen.append(eid)
        selected_events.append((eid, kind))
        if len(distinct_items_seen) >= 4:
            break
    if len(distinct_items_seen) < 2:
        return associations

    # De-duplicate for the final citation list/text - an item that
    # appears as both a blocker and a scope event should be named
    # once, not twice, even though it already counted toward the
    # distinctness check above.
    seen_final = []
    deduped_events = []
    for eid, kind in selected_events:
        if eid not in seen_final:
            seen_final.append(eid)
            deduped_events.append((eid, kind))

    cited_ids = [eid for eid, _ in deduped_events]
    kinds = ", ".join(f"{eid} ({kind})" for eid, kind in deduped_events)

    description = (
        f"Velocity {velocity_direction} during a period that also saw the following events: {kinds}. "
        f"This states temporal coincidence only, not a proven cause."
    )
    associations.append(TemporalAssociation(cited_item_ids=cited_ids, description=description))
    return associations


def extract_delivery_narrative_facts(snapshot: Snapshot) -> DeliveryNarrativeFacts:
    weekly_facts = extract_weekly_report_facts(snapshot)

    period_start = date.fromisoformat(weekly_facts.week_start)
    period_end = date.fromisoformat(weekly_facts.week_end)

    velocity_direction = None
    if weekly_facts.prior_period_velocity_rate is not None:
        velocity_direction = _classify_velocity_change(
            weekly_facts.velocity_rate, weekly_facts.prior_period_velocity_rate
        )

    blocker_periods = _compute_blocker_periods(snapshot, period_start, period_end)
    scope_events = _compute_scope_events(snapshot, period_start, period_end)
    associations = _compute_associations(blocker_periods, scope_events, velocity_direction)

    return DeliveryNarrativeFacts(
        reference_period_label=weekly_facts.sprint_name,
        reference_period_start=weekly_facts.week_start,
        reference_period_end=weekly_facts.week_end,
        velocity_this_period=weekly_facts.velocity_rate,
        velocity_prior_period=weekly_facts.prior_period_velocity_rate,
        velocity_direction=velocity_direction,
        blocker_periods=blocker_periods,
        scope_events=scope_events,
        associations=associations,
        item_titles=weekly_facts.item_titles,
    )
