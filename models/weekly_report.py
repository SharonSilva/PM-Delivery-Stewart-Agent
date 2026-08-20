from datetime import date
from typing import Optional
from pydantic import BaseModel


class RankedRisk(BaseModel):
    """A risk entry, carried through with its real fields, ranked
    by impact for the report."""
    id: str
    description: str
    impact: str
    item_id: Optional[str] = None
    owner: Optional[str] = None


class ScopeChangeItem(BaseModel):
    item_id: str
    title: str
    created_at: str


class WeeklyReportFacts(BaseModel):
    """Pure, deterministic facts for one weekly report. Every field
    traces back to real snapshot/risk-log data - the model only
    narrates this.

    week_start/week_end reflect ACTUAL elapsed time within the
    current sprint, not a fabricated fixed 7-day window - our real
    seed data only spans Sprint 2's first 2 days, and this facts
    layer reports that honestly rather than pretending otherwise.
    """
    sprint_name: str
    week_start: str
    week_end: str
    elapsed_days: int

    items_completed_this_period: list[str] = []   # item IDs done within [week_start, week_end]
    items_completed_count: int = 0
    velocity_rate: float = 0.0  # items completed per elapsed day, THIS period

    prior_period_label: Optional[str] = None       # e.g. "Sprint 1" - None if no comparison basis
    prior_period_days: Optional[int] = None
    prior_period_items_completed: Optional[int] = None
    prior_period_velocity_rate: Optional[float] = None

    scope_added_mid_sprint: list[ScopeChangeItem] = []  # items created after sprint start

    top_risks: list[RankedRisk] = []  # ranked by impact (High > Medium > Low)

    # Risks with no owner - our disclosed, code-level interpretation
    # of "decisions needed from client." This mapping is a stated
    # design choice, not something the data literally labels.
    decisions_needed: list[RankedRisk] = []

    item_titles: dict[str, str] = {}
