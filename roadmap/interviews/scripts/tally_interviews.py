"""Tallies the interview notes of workstream 2.2 against the evidence the GO / NO-GO decision (2.3) asks for.

    python roadmap/interviews/scripts/tally_interviews.py                       # read roadmap/interviews/notes/*.md
    python roadmap/interviews/scripts/tally_interviews.py --notes-dir DIR       # read another folder
    python roadmap/interviews/scripts/tally_interviews.py --include-examples    # also count the FAKE EXAMPLE notes

Every note starts with a front matter block of simple `key: value` lines between two `---` lines (see `notes-template.md`). The keys read here are:

- `pain`: 1 to 5.
- `recurring`: yes or no.
- `would_pay`: yes, maybe or no.
- `amount_inr`: the monthly amount in rupees the person named (optional).
- `commitment`: none, pilot, pre-order or loi.
- `region` and `company_size`: free labels used for the breakdowns.
- `example`: true marks a FAKE EXAMPLE, which is skipped unless `--include-examples` is given. A file name starting with `example` is skipped too.

Values that cannot be read are reported on stderr and counted as unknown. Counting assumes one interview per team (⚠️ if two people from one team were
interviewed, count them once by hand).
"""

import argparse
import statistics
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DEFAULT_NOTES_DIR: Path = Path(__file__).resolve().parent.parent / "notes"
UNKNOWN: str = "unknown"
PAIN_THRESHOLD: int = 4
GO_PAIN_AND_RECURRING: int = 3
GO_PAY_OR_COMMIT: int = 5
VALID_YES_NO: frozenset[str] = frozenset({"yes", "no"})
VALID_WOULD_PAY: frozenset[str] = frozenset({"yes", "maybe", "no"})
VALID_COMMITMENT: frozenset[str] = frozenset({"none", "pilot", "pre-order", "loi"})


@dataclass
class Interview:
    """One interview note, reduced to the fields that are tallied.

    Attributes:
        name: The file name of the note.
        pain: Pain intensity from 1 to 5, or None when missing or invalid.
        recurring: True for a recurring problem, False for no, None when unknown.
        would_pay: yes, maybe, no, or None when unknown.
        amount_inr: Monthly amount in rupees the person named, or None.
        commitment: none, pilot, pre-order or loi, or None when unknown.
        region: Free label for the region, "unknown" when missing.
        company_size: Free label for the company size in developers, "unknown" when missing.
    """

    name: str
    pain: Optional[int]
    recurring: Optional[bool]
    would_pay: Optional[str]
    amount_inr: Optional[int]
    commitment: Optional[str]
    region: str
    company_size: str


def parse_front_matter(text: str) -> dict[str, str]:
    """Reads the `key: value` lines between the first two `---` lines of a note.

    Blank lines and lines starting with `#` are ignored, and so is a trailing ` # comment`. Keys are lower-cased.

    Args:
        text: The whole text of the note.

    Returns:
        The key and value pairs, empty when the note has no complete front matter block.
    """
    lines: list[str] = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return values
        stripped: str = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        values[key.strip().lower()] = value.split(" #")[0].strip()
    return {}


def _choice(values: dict[str, str], key: str, allowed: frozenset[str], name: str, warnings: list[str]) -> Optional[str]:
    """Returns the lower-cased value of `key` if it is allowed, else None (and a warning when it was filled in wrongly)."""
    value: str = values.get(key, "").lower()
    if not value:
        return None
    if value not in allowed:
        warnings.append(f"{name}: invalid {key} '{value}' (expected one of {', '.join(sorted(allowed))})")
        return None
    return value


def _integer(values: dict[str, str], key: str, name: str, warnings: list[str]) -> Optional[int]:
    """Returns the integer value of `key`, else None (and a warning when it was filled in wrongly)."""
    value: str = values.get(key, "")
    if not value:
        return None
    try:
        return int(value.replace(",", ""))
    except ValueError:
        warnings.append(f"{name}: invalid {key} '{value}' (expected a whole number)")
        return None


def build_interview(name: str, values: dict[str, str], warnings: list[str]) -> Interview:
    """Turns the front matter of one note into an `Interview`.

    Args:
        name: The file name of the note, used in warnings.
        values: The parsed front matter.
        warnings: Collects a message for every value that is filled in but cannot be read.

    Returns:
        The interview, with None for every missing or invalid value.
    """
    pain: Optional[int] = _integer(values, "pain", name, warnings)
    if pain is not None and not 1 <= pain <= 5:
        warnings.append(f"{name}: pain {pain} is outside 1 to 5")
        pain = None
    recurring_text: Optional[str] = _choice(values, "recurring", VALID_YES_NO, name, warnings)
    return Interview(
        name=name,
        pain=pain,
        recurring=None if recurring_text is None else recurring_text == "yes",
        would_pay=_choice(values, "would_pay", VALID_WOULD_PAY, name, warnings),
        amount_inr=_integer(values, "amount_inr", name, warnings),
        commitment=_choice(values, "commitment", VALID_COMMITMENT, name, warnings),
        region=values.get("region", "").lower() or UNKNOWN,
        company_size=values.get("company_size", "").lower() or UNKNOWN,
    )


def load_interviews(notes_dir: Path, include_examples: bool, warnings: list[str]) -> list[Interview]:
    """Reads every `*.md` note of a folder, in file name order.

    Args:
        notes_dir: The folder with the notes.
        include_examples: Count notes marked as examples too.
        warnings: Collects a message for every value that cannot be read.

    Returns:
        One `Interview` per note. Notes without a front matter block are reported in `warnings` and skipped, and so are examples unless asked for.
    """
    interviews: list[Interview] = []
    for path in sorted(notes_dir.glob("*.md")):
        values: dict[str, str] = parse_front_matter(path.read_text(encoding="utf-8"))
        if not values:
            warnings.append(f"{path.name}: no front matter block, skipped")
            continue
        is_example: bool = path.name.lower().startswith("example") or values.get("example", "").lower() == "true"
        if is_example and not include_examples:
            continue
        interviews.append(build_interview(path.name, values, warnings))
    return interviews


def is_pain_and_recurring(interview: Interview) -> bool:
    """True when the person rates the pain at 4 or more and describes a recurring problem."""
    return interview.pain is not None and interview.pain >= PAIN_THRESHOLD and interview.recurring is True


def is_pay_or_commit(interview: Interview) -> bool:
    """True when the person would pay (yes) or agreed to any commitment (pilot, pre-order or LOI)."""
    return interview.would_pay == "yes" or interview.commitment in {"pilot", "pre-order", "loi"}


def format_report(interviews: list[Interview]) -> str:
    """Formats the counts that feed the 2.3 criteria.

    Args:
        interviews: The interviews to count.

    Returns:
        A plain text report.
    """
    pain_and_recurring: int = sum(1 for item in interviews if is_pain_and_recurring(item))
    would_pay_yes: int = sum(1 for item in interviews if item.would_pay == "yes")
    would_pay_maybe: int = sum(1 for item in interviews if item.would_pay == "maybe")
    commitments: Counter[str] = Counter(item.commitment for item in interviews if item.commitment in {"pilot", "pre-order", "loi"})
    any_commitment: int = sum(commitments.values())
    pay_or_commit: int = sum(1 for item in interviews if is_pay_or_commit(item))
    amounts: list[int] = [item.amount_inr for item in interviews if item.amount_inr is not None and item.would_pay in {"yes", "maybe"}]

    lines: list[str] = [f"Interviews counted: {len(interviews)}", "", "2.3 criteria (rules of thumb, not sourced benchmarks)"]
    lines.append(f"  Pain >= {PAIN_THRESHOLD} and a recurring problem: {pain_and_recurring} / {GO_PAIN_AND_RECURRING} needed")
    lines.append(f"  Would pay = yes: {would_pay_yes} (maybe: {would_pay_maybe})")
    commitment_detail: str = ", ".join(f"{kind}: {commitments[kind]}" for kind in sorted(commitments)) or "none"
    lines.append(f"  Any commitment (pilot, pre-order or LOI): {any_commitment} ({commitment_detail})")
    lines.append(f"  Would pay (yes) or commit: {pay_or_commit} / {GO_PAY_OR_COMMIT} needed")
    if amounts:
        lines.append(f"  Monthly amounts named by yes or maybe (INR): min {min(amounts)}, median {statistics.median(amounts):g}, max {max(amounts)}")
    else:
        lines.append("  Monthly amounts named by yes or maybe (INR): none recorded")
    lines.append("")
    lines.extend(_breakdown("Region", [item.region for item in interviews], interviews))
    lines.append("")
    lines.extend(_breakdown("Company size (developers)", [item.company_size for item in interviews], interviews))
    return "\n".join(lines)


def _breakdown(title: str, labels: list[str], interviews: list[Interview]) -> list[str]:
    """Formats one breakdown table: interviews, pain >= 4 with recurring, and pay or commit per label."""
    lines: list[str] = [f"{title}:", f"  {'':<14} {'interviews':>10} {'pain>=4+recurring':>18} {'pay or commit':>14}"]
    for label in sorted(set(labels)):
        group: list[Interview] = [item for item, value in zip(interviews, labels) if value == label]
        pain: int = sum(1 for item in group if is_pain_and_recurring(item))
        pay: int = sum(1 for item in group if is_pay_or_commit(item))
        lines.append(f"  {label:<14} {len(group):>10} {pain:>18} {pay:>14}")
    return lines


def main(argv: Optional[list[str]] = None) -> int:
    """Runs the tally.

    Args:
        argv: The command line arguments, `sys.argv[1:]` when None.

    Returns:
        The exit code: 0 on success, 2 when the notes folder does not exist.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Tally the interview notes against the 2.3 GO criteria.")
    parser.add_argument("--notes-dir", type=Path, default=DEFAULT_NOTES_DIR, help="Folder with the notes (default: roadmap/interviews/notes).")
    parser.add_argument("--include-examples", action="store_true", help="Also count the FAKE EXAMPLE notes.")
    args: argparse.Namespace = parser.parse_args(argv)

    if not args.notes_dir.is_dir():
        print(f"Notes folder not found: {args.notes_dir}", file=sys.stderr)
        return 2
    warnings: list[str] = []
    interviews: list[Interview] = load_interviews(args.notes_dir, args.include_examples, warnings)
    for message in warnings:
        print(f"warning: {message}", file=sys.stderr)
    print(format_report(interviews))
    return 0


if __name__ == "__main__":
    sys.exit(main())
