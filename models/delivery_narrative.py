from typing import Optional
from pydantic import BaseModel


class BlockerPeriod(BaseModel):
    item_id: str
    title: str
    blocked_from: str
    blocked_until: Optional[str] = None  # None if still blocked as of the reference date
    days_blocked: int


class ScopeEvent(BaseModel):
    item_id: str
    title: str
    event_date: str


class TemporalAssociation(BaseModel):
    """A computed, code-derived temporal coincidence - NOT a causal
    claim. Two or more real events (blocker periods, scope changes)
    whose dates overlap the reference period. The narration layer
    is only permitted to describe THIS, never to invent a cause
    beyond what's listed here."""
    cited_item_ids: list[str]
    description: str  # factual, code-generated description of the coincidence


class DeliveryNarrativeFacts(BaseModel):
    reference_period_label: str
    reference_period_start: str
    reference_period_end: str

    velocity_this_period: float
    velocity_prior_period: Optional[float] = None
    velocity_direction: Optional[str] = None  # "increased" / "decreased" / "stayed similar" / None

    blocker_periods: list[BlockerPeriod] = []
    scope_events: list[ScopeEvent] = []
    associations: list[TemporalAssociation] = []

    item_titles: dict[str, str] = {}
