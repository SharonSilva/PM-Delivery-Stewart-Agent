"""
Shared prompt-loading utility. Each capability's prompt lives in its
own file under prompts/, loaded here at runtime rather than being
an inline f-string scattered through the narration services. Uses
simple {{TOKEN}} placeholder substitution (not str.format()) so
literal JSON braces in a prompt's schema example never need
escaping.
"""
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str, **substitutions: str) -> str:
    """Loads prompts/{name}.txt and replaces every {{KEY}} placeholder
    with the corresponding keyword argument's value."""
    path = _PROMPTS_DIR / f"{name}.txt"
    template = path.read_text()
    for key, value in substitutions.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    return template
