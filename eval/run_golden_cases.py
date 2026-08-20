"""
Runs all implemented golden test cases and prints/writes one line
per metric with measured value and target. Run with:
    python3.11 eval/run_golden_cases.py
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.golden_cases import (
    golden_case_1_citation_rate,
    golden_case_2_fabrication_probe,
    golden_case_9_determinism,
)

CASES = [
    ("Golden Case 1: Citation rate", golden_case_1_citation_rate),
    ("Golden Case 2: Fabrication probe", golden_case_2_fabrication_probe),
    ("Golden Case 9: Determinism", golden_case_9_determinism),
]


def main():
    lines = [f"Eval run at {datetime.now().isoformat()}", ""]
    any_failed = False

    for name, fn in CASES:
        passed, measured, target, detail = fn()
        status = "PASS" if passed else "FAIL"
        line = f"[{status}] {name}: measured={measured} target={target} | {detail}"
        print(line)
        lines.append(line)
        if not passed:
            any_failed = True

    lines.append("")
    lines.append(f"Overall: {'ALL PASSED' if not any_failed else 'SOME FAILED'}")
    print()
    print(lines[-1])

    with open("eval/results.txt", "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
