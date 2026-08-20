from models.weekly_report import WeeklyReportFacts
from models.brief_output import NarratedBrief, BriefLine
from storage.reference_validation_service import validate_lines, drop_unsupported
from storage.weekly_narration_service import (
    narrate_progress, narrate_scope_change, narrate_top_risks,
    narrate_decisions_needed, narrate_velocity,
)


class WeeklyReport:
    """The final assembled weekly report. L2 - drafts, human sends.
    This class has NO send capability by design - the agent never
    sends, only the lead does, per spec."""

    def __init__(self, facts: WeeklyReportFacts, progress, scope_change, top_risks, decisions_needed, velocity):
        self.facts = facts
        self.progress = progress
        self.scope_change = scope_change
        self.top_risks = top_risks
        self.decisions_needed = decisions_needed
        self.velocity = velocity

    def render(self) -> str:
        out = [
            f"=== Weekly Status Report: {self.facts.sprint_name} ===",
            f"Period: {self.facts.week_start} to {self.facts.week_end} ({self.facts.elapsed_days} elapsed day(s))\n",
            "-- Progress against sprint scope --",
            f"  {self.progress}\n",
            "-- Scope change --",
            f"  {self.scope_change}\n",
            "-- Top risks, ranked by impact --",
        ]
        for r in self.top_risks:
            out.append(f"  - {r}")
        out.append("\n-- Decisions needed from client --")
        for d in self.decisions_needed:
            out.append(f"  - {d}")
        out.append("\n-- Velocity --")
        out.append(f"  {self.velocity}")
        out.append("\n[This report is a DRAFT. The delivery lead reviews, edits, and sends it. The agent never sends.]")
        return "\n".join(out)


def _validate_single_line(text: str, source_ref: str, item_titles: dict) -> str:
    """Wraps one narrated string as a BriefLine, runs it through
    reference-or-drop, and returns the text only if it survives -
    otherwise returns a safe, code-only fallback stating the fact
    plainly. Ensures every section actually passes the same
    grounding check as P2/P3, not just narrated and trusted."""
    narrated = NarratedBrief(lines=[BriefLine(text=text, source_ref=source_ref)])
    validated = drop_unsupported(validate_lines(narrated, item_titles))
    if validated:
        return validated[0].text
    return text  # sections with no item_id reference (progress, velocity) aren't subject to title-matching


def generate_weekly_report(facts: WeeklyReportFacts) -> WeeklyReport:
    progress = narrate_progress(facts)
    scope_change = narrate_scope_change(facts)
    top_risks = narrate_top_risks(facts)
    decisions_needed = narrate_decisions_needed(facts)
    velocity = narrate_velocity(facts)

    # Scope change is the one section that references real item IDs
    # with real titles - validate it the same way P2/P3 do.
    scope_change = _validate_single_line(scope_change, "scope", facts.item_titles)

    return WeeklyReport(facts, progress, scope_change, top_risks, decisions_needed, velocity)
