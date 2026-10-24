"""Tests for `roadmap/interviews/scripts/tally_interviews.py`, which counts the interview notes against the 2.3 GO criteria.

The script lives outside the package, so it is imported by path. The notes are written to temporary folders; the committed notes are never read.
"""

import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path
from types import ModuleType

ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT: str = os.path.join(ROOT, "roadmap", "interviews", "scripts", "tally_interviews.py")
COMMITTED_NOTES: str = os.path.join(ROOT, "roadmap", "interviews", "notes")


def load_script() -> ModuleType:
    """Imports the tally script by path"""
    spec = importlib.util.spec_from_file_location("tally_interviews", SCRIPT)
    assert spec is not None and spec.loader is not None
    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def note(**fields: str) -> str:
    """Builds a note with a front matter block from the given fields"""
    lines: list[str] = ["---"] + [f"{key}: {value}" for key, value in fields.items()] + ["---", "", "Body text."]
    return "\n".join(lines)


class TallyInterviewsTests(unittest.TestCase):
    """Tests of parsing, loading, counting and the command line"""

    def setUp(self) -> None:
        self.tally: ModuleType = load_script()
        self._tmp: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.notes_dir: Path = Path(self._tmp.name)

    def write(self, name: str, text: str) -> None:
        """Writes a note into the temporary notes folder"""
        (self.notes_dir / name).write_text(text, encoding="utf-8")

    def write_sample_notes(self) -> None:
        """Writes four real notes and one fake example"""
        self.write(
            "INT-001.md",
            note(pain="5", recurring="yes", would_pay="yes", amount_inr="1,499", commitment="pilot", region="India", company_size="50-200"),
        )
        self.write(
            "INT-002.md",
            note(pain="4", recurring="no", would_pay="maybe", amount_inr="999", commitment="none", region="india", company_size="10-49"),
        )
        self.write("INT-003.md", note(pain="4", recurring="yes", would_pay="no", commitment="loi", region="emea", company_size="10-49"))
        self.write("INT-004.md", note(pain="2", recurring="no", would_pay="no", commitment="none"))
        self.write("example-fake.md", note(example="true", pain="5", recurring="yes", would_pay="yes", commitment="pilot", region="india"))

    def test_parse_front_matter_reads_key_value_lines(self) -> None:
        text: str = "---\n# a comment\nPain: 4 # note\n\nregion: india\nno colon here\n---\nbody: ignored\n"
        self.assertEqual(self.tally.parse_front_matter(text), {"pain": "4", "region": "india"})

    def test_parse_front_matter_needs_a_complete_block(self) -> None:
        self.assertEqual(self.tally.parse_front_matter(""), {})
        self.assertEqual(self.tally.parse_front_matter("no front matter\n"), {})
        self.assertEqual(self.tally.parse_front_matter("---\npain: 4\n"), {})

    def test_build_interview_reads_valid_values(self) -> None:
        warnings: list[str] = []
        values: dict[str, str] = {"pain": "4", "recurring": "YES", "would_pay": "maybe", "amount_inr": "1,499", "commitment": "pre-order", "region": "India"}
        interview = self.tally.build_interview("a.md", values, warnings)
        self.assertEqual((interview.pain, interview.recurring, interview.would_pay, interview.amount_inr), (4, True, "maybe", 1499))
        self.assertEqual((interview.commitment, interview.region, interview.company_size), ("pre-order", "india", "unknown"))
        self.assertEqual(warnings, [])

    def test_build_interview_treats_missing_values_as_unknown_without_warnings(self) -> None:
        warnings: list[str] = []
        interview = self.tally.build_interview("a.md", {}, warnings)
        self.assertEqual((interview.pain, interview.recurring, interview.would_pay, interview.amount_inr, interview.commitment), (None,) * 5)
        self.assertEqual(warnings, [])

    def test_build_interview_warns_about_invalid_values(self) -> None:
        warnings: list[str] = []
        values: dict[str, str] = {"pain": "9", "recurring": "sometimes", "would_pay": "perhaps", "amount_inr": "lots", "commitment": "handshake"}
        interview = self.tally.build_interview("a.md", values, warnings)
        self.assertEqual((interview.pain, interview.recurring, interview.would_pay, interview.amount_inr, interview.commitment), (None,) * 5)
        self.assertEqual(len(warnings), 5)
        self.assertTrue(any("outside 1 to 5" in message for message in warnings))
        self.assertTrue(any("whole number" in message for message in warnings))

    def test_load_interviews_skips_examples_by_default(self) -> None:
        self.write_sample_notes()
        warnings: list[str] = []
        names: list[str] = [item.name for item in self.tally.load_interviews(self.notes_dir, False, warnings)]
        self.assertEqual(names, ["INT-001.md", "INT-002.md", "INT-003.md", "INT-004.md"])
        self.assertEqual(warnings, [])

    def test_load_interviews_includes_examples_on_request(self) -> None:
        self.write_sample_notes()
        names: list[str] = [item.name for item in self.tally.load_interviews(self.notes_dir, True, [])]
        self.assertIn("example-fake.md", names)
        self.assertEqual(len(names), 5)

    def test_load_interviews_skips_a_note_marked_as_an_example_by_its_front_matter(self) -> None:
        self.write("INT-009.md", note(example="True", pain="5"))
        self.assertEqual(self.tally.load_interviews(self.notes_dir, False, []), [])
        self.assertEqual(len(self.tally.load_interviews(self.notes_dir, True, [])), 1)

    def test_load_interviews_warns_about_a_note_without_front_matter(self) -> None:
        self.write("INT-010.md", "Just text, no front matter.")
        self.write("notes.txt", note(pain="5"))
        warnings: list[str] = []
        self.assertEqual(self.tally.load_interviews(self.notes_dir, False, warnings), [])
        self.assertEqual(warnings, ["INT-010.md: no front matter block, skipped"])

    def test_criteria_predicates(self) -> None:
        build = self.tally.build_interview
        painful = build("a", {"pain": "4", "recurring": "yes"}, [])
        self.assertTrue(self.tally.is_pain_and_recurring(painful))
        self.assertFalse(self.tally.is_pain_and_recurring(build("a", {"pain": "3", "recurring": "yes"}, [])))
        self.assertFalse(self.tally.is_pain_and_recurring(build("a", {"pain": "5", "recurring": "no"}, [])))
        self.assertFalse(self.tally.is_pain_and_recurring(build("a", {"recurring": "yes"}, [])))
        self.assertTrue(self.tally.is_pay_or_commit(build("a", {"would_pay": "yes"}, [])))
        self.assertTrue(self.tally.is_pay_or_commit(build("a", {"would_pay": "no", "commitment": "loi"}, [])))
        self.assertFalse(self.tally.is_pay_or_commit(build("a", {"would_pay": "maybe", "commitment": "none"}, [])))

    def test_format_report_counts_the_criteria_and_breakdowns(self) -> None:
        self.write_sample_notes()
        report: str = self.tally.format_report(self.tally.load_interviews(self.notes_dir, False, []))
        self.assertIn("Interviews counted: 4", report)
        self.assertIn("Pain >= 4 and a recurring problem: 2 / 3 needed", report)
        self.assertIn("Would pay = yes: 1 (maybe: 1)", report)
        self.assertIn("Any commitment (pilot, pre-order or LOI): 2 (loi: 1, pilot: 1)", report)
        self.assertIn("Would pay (yes) or commit: 2 / 5 needed", report)
        self.assertIn("min 999, median 1249, max 1499", report)
        self.assertRegex(report, r"india\s+2\s+1\s+1")
        self.assertRegex(report, r"emea\s+1\s+1\s+1")
        self.assertRegex(report, r"unknown\s+1\s+0\s+0")
        self.assertRegex(report, r"10-49\s+2\s+1\s+1")

    def test_format_report_without_interviews(self) -> None:
        report: str = self.tally.format_report([])
        self.assertIn("Interviews counted: 0", report)
        self.assertIn("Any commitment (pilot, pre-order or LOI): 0 (none)", report)
        self.assertIn("none recorded", report)

    def run_main(self, argv: list[str]) -> tuple[int, str, str]:
        """Runs `main` and returns the exit code, stdout and stderr"""
        out: io.StringIO = io.StringIO()
        err: io.StringIO = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code: int = self.tally.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_main_skips_examples_unless_asked(self) -> None:
        self.write_sample_notes()
        self.write("INT-011.md", "no front matter")
        code, out, err = self.run_main(["--notes-dir", str(self.notes_dir)])
        self.assertEqual(code, 0)
        self.assertIn("Interviews counted: 4", out)
        self.assertIn("warning: INT-011.md: no front matter block, skipped", err)
        code, out, _ = self.run_main(["--notes-dir", str(self.notes_dir), "--include-examples"])
        self.assertEqual(code, 0)
        self.assertIn("Interviews counted: 5", out)

    def test_main_reports_a_missing_folder(self) -> None:
        code, out, err = self.run_main(["--notes-dir", str(self.notes_dir / "missing")])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("Notes folder not found", err)

    def test_committed_notes_count_no_real_interviews_while_only_the_example_exists(self) -> None:
        self.assertTrue(os.path.isfile(os.path.join(COMMITTED_NOTES, "example-fake.md")))
        interviews = self.tally.load_interviews(Path(COMMITTED_NOTES), False, [])
        self.assertTrue(all(not item.name.startswith("example") for item in interviews))
        with_examples = self.tally.load_interviews(Path(COMMITTED_NOTES), True, [])
        self.assertEqual(len(with_examples), len(interviews) + 1)


if __name__ == "__main__":
    unittest.main()
