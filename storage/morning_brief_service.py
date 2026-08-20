from datetime import datetime
from models.brief_facts import BriefFacts
from storage.brief_facts_service import extract_brief_facts
from storage.brief_narration_service import narrate_person_status
from storage.brief_blocker_narration_service import narrate_blocker
from storage.reference_validation_service import validate_lines,drop_unsupported

class MorningBrief:
    """The final assembled brief, structured per P2's required
    output shape: sprint header, then per-person, then blockers
    ranked by impact."""

    def __init__(self, facts: BriefFacts, person_lines: dict, blocker_lines: dict):
        self.facts = facts
        self.person_lines = person_lines    # person -> list[str]
        self.blocker_lines = blocker_lines  # item_id -> str
        
    def render(self) -> str:
        out = [f" Morning Brief: {self.facts.sprint_name}, Day {self.facts.sprint_day}/{self.facts.sprint_total_days} \n"]

        out.append("Per-person status ")
        for person, lines in self.person_lines.items():
            out.append(f"{person}:")
            for line in lines:
                out.append(f"  - {line}")

        out.append("\n Blockers, ranked by impact ")
        for item_id, text in self.blocker_lines.items():
            out.append(f"  - {text}")

        return "\n".join(out)


def generate_morning_brief(facts: BriefFacts) -> MorningBrief:
    """Runs the full P2 pipeline: for each person and each blocker,
    narrate then validate via reference-or-drop, keeping only
    supported lines. Facts (stage 1) are assumed already extracted
    by the caller, since determinism depends on the same facts
    being reused rather than re-derived."""

    person_lines: dict[str, list[str]] = {}
    for person in facts.people:
        narrated = narrate_person_status(person, facts.item_titles)
        validated = drop_unsupported(validate_lines(narrated, facts.item_titles, extra_known_refs={p.person for p in facts.people}))
        person_lines[person.person] = [line.text for line in validated]

    blocker_lines: dict[str, str] = {}
    for blocker in facts.blockers:
        narrated = narrate_blocker(blocker)
        validated = drop_unsupported(validate_lines(narrated, facts.item_titles, extra_known_refs={p.person for p in facts.people}))
        if validated:
            blocker_lines[blocker.item_id] = validated[0].text

    return MorningBrief(facts, person_lines, blocker_lines)