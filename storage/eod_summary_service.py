from models.eod_delta import EODDeltaFacts
from models.brief_output import NarratedBrief
from storage.eod_narration_service import narrate_item_delta_raw
from storage.reference_validation_service import validate_lines, drop_unsupported


class EODSummary:
    def __init__(self, facts: EODDeltaFacts, shipped_lines, blocked_lines, other_lines):
        self.facts = facts
        self.shipped_lines = shipped_lines
        self.blocked_lines = blocked_lines
        self.other_lines = other_lines

    def render(self) -> str:
        out = [f"=== End-of-Day Summary: {self.facts.sprint_name}, Day {self.facts.sprint_day} ===\n"]

        out.append(f"-- Shipped today ({len(self.shipped_lines)}) --")
        for line in self.shipped_lines:
            out.append(f"  - {line}")

        out.append(f"\n-- Newly blocked ({len(self.blocked_lines)}) --")
        for line in self.blocked_lines:
            out.append(f"  - {line}")

        out.append(f"\n-- Other changes today ({len(self.other_lines)}) --")
        for line in self.other_lines:
            out.append(f"  - {line}")

        out.append(f"\n-- Still pending, no change today: {len(self.facts.still_pending)} items --")

        if self.facts.meeting_outcomes_today:
            out.append(f"\n-- Meeting outcomes today ({len(self.facts.meeting_outcomes_today)}) --")
            for m in self.facts.meeting_outcomes_today:
                status = "consent given (not yet processed)" if m.consent else "REFUSED (no consent)"
                out.append(f"  - {m.meeting_id} [{status}]: {'; '.join(m.decision_texts)}")

        return "\n".join(out)


def _narrate_and_validate(deltas, item_titles) -> list[str]:
    """Narrates each delta, then runs reference-or-drop before
    returning only supported lines - a delta with an unsupported
    narration is DROPPED rather than shown unverified."""
    texts = []
    for delta in deltas:
        line = narrate_item_delta_raw(delta)
        validated = drop_unsupported(validate_lines(NarratedBrief(lines=[line]), item_titles))
        if validated:
            texts.append(validated[0].text)
        else:
            # Fallback: fully grounded, code-only description, never dropped silently
            texts.append(f"{delta.morning_status} -> {delta.eod_status}: {delta.item_id} (\"{delta.title}\")")
    return texts


def generate_eod_summary(facts: EODDeltaFacts) -> EODSummary:
    shipped_lines = _narrate_and_validate(facts.shipped, facts.item_titles)
    blocked_lines = _narrate_and_validate(facts.newly_blocked, facts.item_titles)
    other_lines = _narrate_and_validate(facts.changed_other, facts.item_titles)
    return EODSummary(facts, shipped_lines, blocked_lines, other_lines)
