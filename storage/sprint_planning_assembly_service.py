from models.sprint_planning import SprintPlanningFacts
from storage.sprint_planning_narration_service import (
    narrate_carry_over_summary, narrate_candidate_slice_summary,
)


class SprintPlanningPack:
    """L2 - drafts, human approves. Deliberately has NO Proposal/
    write-execution path: per spec this is 'never applied to the
    tracker automatically', so there is no write to gate - building
    a Proposal object here would imply an action that doesn't
    exist."""

    def __init__(self, facts: SprintPlanningFacts, carry_over_summary: str, candidate_summary: str):
        self.facts = facts
        self.carry_over_summary = carry_over_summary
        self.candidate_summary = candidate_summary

    def render(self) -> str:
        f = self.facts
        out = [
            f"=== Sprint Planning Pack (reference: {f.reference_sprint_name}, "
            f"{f.reference_sprint_start} to {f.reference_sprint_end}) ===\n",
            f"-- Carry-over ({len(f.carry_over)}) --",
            f"  {self.carry_over_summary}",
        ]
        for c in f.carry_over:
            out.append(f"  - {c.item_id} (\"{c.title}\"): {c.status_at_sprint_end}, assignee={c.assignee or 'unassigned'}")

        out.append(f"\n-- Capacity --")
        out.append(f"  {f.capacity_is_assumption_note}")

        out.append(f"\n-- Candidate slice ({len(f.candidate_slice)}) --")
        out.append(f"  {self.candidate_summary}")
        for s in f.candidate_slice:
            out.append(f"  - {s.item_id} (\"{s.title}\"): {s.reasoning}")

        out.append(f"\n-- Remaining backlog ({len(f.ready_backlog)}) --")
        for b in f.ready_backlog[:5]:
            out.append(f"  - {b.item_id} (\"{b.title}\"), priority={b.priority or 'unset'}")
        if len(f.ready_backlog) > 5:
            out.append(f"  ... and {len(f.ready_backlog) - 5} more")

        out.append("\n[This is a DRAFT for review before planning. Never applied to the tracker automatically.]")
        return "\n".join(out)


def generate_sprint_planning_pack(facts: SprintPlanningFacts) -> SprintPlanningPack:
    carry_over_summary = narrate_carry_over_summary(facts)
    candidate_summary = narrate_candidate_slice_summary(facts)
    return SprintPlanningPack(facts, carry_over_summary, candidate_summary)
