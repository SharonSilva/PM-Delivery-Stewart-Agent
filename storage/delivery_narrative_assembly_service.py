from models.delivery_narrative import DeliveryNarrativeFacts
from storage.delivery_narrative_narration_service import narrate_association


class DeliveryNarrative:
    """L3 - acts, human reviews. Per spec: 'Reviewed before it
    reaches anyone outside the team.' No send capability - this is
    an internal artifact for the team/lead to review, same
    no-fabricated-write-path principle as P10."""

    def __init__(self, facts: DeliveryNarrativeFacts, narrated_associations: list[str]):
        self.facts = facts
        self.narrated_associations = narrated_associations

    def render(self) -> str:
        f = self.facts
        out = [
            f"=== Delivery Narrative: {f.reference_period_label} "
            f"({f.reference_period_start} to {f.reference_period_end}) ===\n",
            f"Velocity: {f.velocity_this_period} items/day"
            + (f" (prior: {f.velocity_prior_period} items/day, {f.velocity_direction})"
               if f.velocity_direction else " (no prior period for comparison)"),
        ]

        if not self.narrated_associations:
            out.append(
                "\nNo notable temporal coincidences were found between blocker/scope "
                "events and the velocity change this period - either velocity stayed "
                "similar, or fewer than 2 distinct related events occurred."
            )
        else:
            out.append("\n-- Observations (temporal coincidence, not proven cause) --")
            for text in self.narrated_associations:
                out.append(f"  - {text}")

        out.append("\n-- Supporting evidence --")
        out.append(f"Blocker periods this window ({len(f.blocker_periods)}):")
        for b in f.blocker_periods:
            out.append(f"  - {b.item_id} (\"{b.title}\"): {b.blocked_from} to {b.blocked_until or 'ongoing'}")
        out.append(f"Scope events this window ({len(f.scope_events)}):")
        for s in f.scope_events:
            out.append(f"  - {s.item_id} (\"{s.title}\") added {s.event_date}")

        out.append("\n[Reviewed before it reaches anyone outside the team.]")
        return "\n".join(out)


def generate_delivery_narrative(facts: DeliveryNarrativeFacts) -> DeliveryNarrative:
    narrated = [narrate_association(a) for a in facts.associations]
    return DeliveryNarrative(facts, narrated)
