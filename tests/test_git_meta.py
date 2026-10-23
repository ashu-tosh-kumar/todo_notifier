import ntpath
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from datetime import date, timedelta
from typing import Optional
from unittest.mock import patch

from todonotifier import git_meta
from todonotifier.git_meta import (
    INFO_UNCOMMITTED,
    WARNING_GIT_NOT_INSTALLED,
    WARNING_NOT_A_GIT_REPO,
    WARNING_SHALLOW_CLONE,
    WARNING_UNSAFE_REPO,
    BlameLine,
    GitError,
    _decode_paths,
    _unquote_diff_path,
    blame_file,
    blame_files,
    changed_lines,
    detect_commit_sha,
    detect_repo_web_url,
    enrich_with_git,
    filter_git_listed,
    find_git_root,
    is_shallow_repository,
    list_git_files,
    normalize_remote_url,
    parse_blame_porcelain,
    parse_changed_lines,
    to_repo_path,
)
from todonotifier.results import TodoItem
from todonotifier.scanner import scan
from todonotifier.settings import ScanSettings

TODAY = date(2025, 6, 15)
OLD_DAY = TODAY - timedelta(days=100)
RECENT_DAY = TODAY - timedelta(days=10)
LOGGER_NAME = "todonotifier.git_meta"
GIT_AVAILABLE = shutil.which("git") is not None

ALICE = ("Alice Anderson", "Alice@Example.com")
BOB = ("Bob Brown", "bob@example.com")

SHA_A = "a" * 40
SHA_B = "b" * 40
ZERO_SHA = "0" * 40
PORCELAIN = (
    f"{SHA_A} 1 1 2\n"
    "author Alice Anderson\n"
    "author-mail <Alice@Example.com>\n"
    "author-time 1735732800\n"  # 2025-01-01T12:00:00Z
    "author-tz +0530\n"
    "committer Alice Anderson\n"
    "summary first\n"
    "filename a.py\n"
    "\t# TODO first\n"
    f"{SHA_A} 2 2\n"
    "\tauthor Not A Header\n"
    f"{SHA_B} 3 3 1\n"
    "author Bob Brown\n"
    "author-mail <bob@example.com>\n"
    "author-time 1738324800\n"  # 2025-01-31T12:00:00Z
    "author-tz -0800\n"
    "summary second\n"
    "boundary\n"
    "filename a.py\n"
    "\tx = 1 y\n"
    f"{ZERO_SHA} 4 4 1\n"
    "author Not Committed Yet\n"
    "author-mail <not.committed.yet>\n"
    "author-time 1750000000\n"
    "filename a.py\n"
    "\tpending\n"
    f"{SHA_A} 5 5 1\n"
    "\tlast\n"
)


def _git_env(name: str, email: str, when: str) -> dict:
    env = dict(os.environ)
    env.update(
        {
            "GIT_AUTHOR_NAME": name,
            "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_NAME": name,
            "GIT_COMMITTER_EMAIL": email,
            "GIT_AUTHOR_DATE": when,
            "GIT_COMMITTER_DATE": when,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
        }
    )
    for key in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_SHA"):
        env.pop(key, None)
    return env


def _iso(day: date) -> str:
    return f"{day.isoformat()}T12:00:00+0000"


def run_git(cwd: str, *args: str, env: Optional[dict] = None) -> str:
    process = subprocess.run(["git", *args], cwd=cwd, env=env or _git_env(*ALICE, _iso(OLD_DAY)), capture_output=True, check=True)
    return process.stdout.decode().strip()


def commit_all(cwd: str, author: tuple, day: date, message: str = "commit") -> None:
    env = _git_env(author[0], author[1], _iso(day))
    run_git(cwd, "add", "-A", env=env)
    run_git(cwd, "commit", "-q", "-m", message, env=env)


class GitTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = os.path.realpath(self._tmp.name)
        env_patch = patch.dict(os.environ, {}, clear=False)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        for key in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_SHA"):
            os.environ.pop(key, None)

    def write(self, rel_path: str, content: str, base: Optional[str] = None) -> str:
        path = os.path.join(base or self.tmp, *rel_path.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return path

    def init_repo(self, path: Optional[str] = None) -> str:
        path = path or self.tmp
        os.makedirs(path, exist_ok=True)
        run_git(path, "init", "-q")
        run_git(path, "config", "commit.gpgsign", "false")
        return path

    def make_two_author_repo(self) -> str:
        """a.py: line 1 (Alice, 100 days ago), line 2 (Bob, 10 days ago), line 3 (Bob, 10 days ago, explicit date, annotated)"""
        self.init_repo()
        self.write("a.py", "# TODO old one\nx = 1\n")
        commit_all(self.tmp, ALICE, OLD_DAY)
        self.write("a.py", "# TODO old one\n# TODO recent one\n# TODO {2030-01-01} @carol annotated\n")
        commit_all(self.tmp, BOB, RECENT_DAY)
        return self.tmp


class TestParseBlamePorcelain(unittest.TestCase):
    def test_should_parse_repeated_commits_and_uncommitted_lines(self):
        blame = parse_blame_porcelain(PORCELAIN, TODAY)

        self.assertEqual({1, 2, 3, 4, 5}, set(blame))
        alice = BlameLine("Alice Anderson", "alice@example.com", date(2025, 1, 1))
        self.assertEqual(alice, blame[1])
        self.assertEqual(alice, blame[2])
        self.assertEqual(alice, blame[5])
        self.assertEqual(BlameLine("Bob Brown", "bob@example.com", date(2025, 1, 31)), blame[3])
        self.assertEqual(BlameLine(None, None, TODAY, committed=False), blame[4])

    def test_should_return_empty_for_empty_output(self):
        self.assertEqual({}, parse_blame_porcelain("", TODAY))

    def test_should_fall_back_to_today_for_unreadable_author_time(self):
        output = f"{SHA_A} 1 1 1\nauthor-time abc\nauthor-mail <>\n\tx\n"

        self.assertEqual(BlameLine(None, None, TODAY), parse_blame_porcelain(output, TODAY)[1])

    @unittest.skipUnless(hasattr(time, "tzset"), "tzset is not available on this platform")
    def test_should_use_utc_dates_regardless_of_timezone(self):
        # 2025-01-01T12:00:00Z is already 2025-01-02 in Kiritimati (UTC+14) and still 2024-12-31 in Honolulu (UTC-10) for other times of day
        for zone in ("Pacific/Kiritimati", "Pacific/Honolulu"):
            with self.subTest(zone=zone), patch.dict(os.environ, {"TZ": zone}):
                time.tzset()
                self.addCleanup(time.tzset)
                self.assertEqual(date(2025, 1, 1), parse_blame_porcelain(PORCELAIN, TODAY)[1].created_date)
                self.assertEqual(date(2025, 1, 31), parse_blame_porcelain(PORCELAIN, TODAY)[3].created_date)


class TestNormalizeRemoteUrl(unittest.TestCase):
    def test_should_normalize_common_forms(self):
        expected = "https://github.com/org/repo"
        for url in (
            "git@github.com:org/repo.git",
            "git@github.com:org/repo",
            "github.com:org/repo.git",
            "ssh://git@github.com/org/repo.git",
            "ssh://git@github.com:22/org/repo.git",
            "https://github.com/org/repo.git",
            "https://github.com/org/repo/",
            "https://user:s3cret@github.com/org/repo.git",
            "https://x-access-token:abc@github.com/org/repo",
            "git://github.com/org/repo.git",
            "  https://GitHub.com/org/repo.git\n",
        ):
            with self.subTest(url=url):
                self.assertEqual(expected, normalize_remote_url(url))

    def test_should_keep_https_port_and_nested_paths(self):
        self.assertEqual("https://git.example.com:8443/group/sub/repo", normalize_remote_url("https://u:p@git.example.com:8443/group/sub/repo.git"))

    def test_should_never_leak_credentials(self):
        for url in ("https://user:s3cret@host.io/o/r.git", "ssh://deploy:s3cret@host.io/o/r.git", "token@host.io:o/r.git"):
            with self.subTest(url=url):
                result = normalize_remote_url(url)
                self.assertNotIn("s3cret", result)
                self.assertNotIn("@", result)
                self.assertNotIn("token", result)

    def test_should_reject_non_hosted_remotes(self):
        for url in (
            "",
            "/srv/git/repo.git",
            "../repo",
            "file:///srv/git/repo.git",
            "https://github.com",
            "ftp://host/o/r",
            "https://host:notaport/o/r",
            "git@host:",
        ):
            with self.subTest(url=url):
                self.assertIsNone(normalize_remote_url(url))


@unittest.skipUnless(GIT_AVAILABLE, "git is not installed")
class TestGitHelpers(GitTestCase):
    def test_find_git_root_should_work_from_file_and_subdirectory(self):
        self.init_repo()
        path = self.write("sub/a.py", "x = 1\n")

        self.assertEqual(self.tmp, find_git_root(path))
        self.assertEqual(self.tmp, find_git_root(os.path.dirname(path)))

    def test_find_git_root_should_return_none_outside_a_repository(self):
        with tempfile.TemporaryDirectory() as outside, patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": os.path.dirname(os.path.realpath(outside))}):
            self.assertIsNone(find_git_root(outside))

    def test_find_git_root_should_return_none_if_git_is_missing(self):
        with patch("todonotifier.git_meta.subprocess.run", side_effect=FileNotFoundError):
            self.assertIsNone(find_git_root(self.tmp))

    def test_find_git_root_should_return_none_on_timeout(self):
        with patch("todonotifier.git_meta.subprocess.run", side_effect=subprocess.TimeoutExpired("git", 10)):
            self.assertIsNone(find_git_root(self.tmp))

    def test_find_git_root_should_return_none_on_os_error(self):
        with patch("todonotifier.git_meta.subprocess.run", side_effect=PermissionError):
            self.assertIsNone(find_git_root(self.tmp))

    def test_find_git_root_should_return_none_for_empty_output(self):
        completed = subprocess.CompletedProcess(["git"], 0, stdout=b"\n", stderr=b"")
        with patch("todonotifier.git_meta.subprocess.run", return_value=completed):
            self.assertIsNone(find_git_root(self.tmp))

    def test_list_git_files_should_list_tracked_and_untracked_but_not_ignored_files(self):
        self.init_repo()
        self.write(".gitignore", "ignored/\n")
        tracked = self.write("a.py", "x = 1\n")
        self.write("ignored/b.py", "x = 2\n")
        untracked = self.write("sub/c.py", "x = 3\n")
        run_git(self.tmp, "add", "a.py")

        files = list_git_files(self.tmp)

        self.assertEqual(sorted([os.path.join(self.tmp, ".gitignore"), tracked, untracked]), files)

    def test_list_git_files_should_list_only_below_the_directory_and_handle_odd_names(self):
        self.init_repo()
        odd = self.write("sub/na\u00efve name\n.py", "x = 1\n")
        self.write("other.py", "x = 2\n")

        self.assertEqual([odd], list_git_files(os.path.join(self.tmp, "sub")))

    def test_list_git_files_should_accept_a_pathspec(self):
        self.init_repo()
        wanted = self.write("a.py", "x = 1\n")
        self.write("b.py", "x = 2\n")

        self.assertEqual([wanted], list_git_files(self.tmp, pathspec="a.py"))
        self.assertEqual([], list_git_files(self.tmp, pathspec="missing.py"))

    def test_list_git_files_should_skip_files_deleted_from_disk(self):
        self.init_repo()
        path = self.write("a.py", "x = 1\n")
        run_git(self.tmp, "add", "a.py")
        os.remove(path)

        self.assertEqual([], list_git_files(self.tmp))

    def test_list_git_files_should_return_none_outside_a_repository(self):
        with tempfile.TemporaryDirectory() as outside, patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": os.path.dirname(os.path.realpath(outside))}):
            self.assertIsNone(list_git_files(outside))

    def test_list_git_files_should_return_none_if_git_is_missing_or_fails(self):
        with patch("todonotifier.git_meta.subprocess.run", side_effect=FileNotFoundError):
            self.assertIsNone(list_git_files(self.tmp))

        self.init_repo()
        with patch("todonotifier.git_meta._run_git", side_effect=[subprocess.CompletedProcess(["git"], 0, stdout=self.tmp.encode(), stderr=b""), None]):
            self.assertIsNone(list_git_files(self.tmp))

        failed = subprocess.CompletedProcess(["git"], 128, stdout=b"", stderr=b"fatal")
        with patch("todonotifier.git_meta._run_git", side_effect=[subprocess.CompletedProcess(["git"], 0, stdout=self.tmp.encode(), stderr=b""), failed]):
            self.assertIsNone(list_git_files(self.tmp))

    def test_is_shallow_repository(self):
        self.init_repo()
        self.write("a.py", "x = 1\n")
        commit_all(self.tmp, ALICE, OLD_DAY)
        self.write("a.py", "x = 2\n")
        commit_all(self.tmp, ALICE, RECENT_DAY)
        self.assertFalse(is_shallow_repository(self.tmp))

        clone = os.path.join(self.tmp, "..", "shallow-" + os.path.basename(self.tmp))
        self.addCleanup(shutil.rmtree, clone, True)
        run_git(self.tmp, "clone", "-q", "--depth", "1", f"file://{self.tmp}", clone)
        self.assertTrue(is_shallow_repository(clone))

    def test_is_shallow_repository_should_be_false_when_git_fails(self):
        with patch("todonotifier.git_meta.subprocess.run", side_effect=FileNotFoundError):
            self.assertFalse(is_shallow_repository(self.tmp))

    def test_detect_repo_web_url_and_commit_sha_from_git(self):
        self.init_repo()
        self.write("a.py", "x = 1\n")
        commit_all(self.tmp, ALICE, OLD_DAY)
        run_git(self.tmp, "remote", "add", "origin", "https://user:s3cret@example.com/org/repo.git")

        self.assertEqual("https://example.com/org/repo", detect_repo_web_url(self.tmp))
        self.assertEqual(run_git(self.tmp, "rev-parse", "HEAD"), detect_commit_sha(self.tmp))

    def test_detect_should_return_none_without_remote_or_commit(self):
        self.init_repo()

        self.assertIsNone(detect_repo_web_url(self.tmp))
        self.assertIsNone(detect_commit_sha(self.tmp))

    def test_detect_should_prefer_github_actions_variables(self):
        self.init_repo()
        run_git(self.tmp, "remote", "add", "origin", "git@example.com:other/other.git")
        sha = "c" * 40
        env = {"GITHUB_SERVER_URL": "https://github.com/", "GITHUB_REPOSITORY": "org/repo", "GITHUB_SHA": sha}

        with patch.dict(os.environ, env):
            self.assertEqual("https://github.com/org/repo", detect_repo_web_url(self.tmp))
            self.assertEqual(sha, detect_commit_sha(self.tmp))

    def test_detect_should_strip_credentials_from_github_server_url(self):
        env = {"GITHUB_SERVER_URL": "https://user:s3cret@ghe.example.com", "GITHUB_REPOSITORY": "org/repo"}

        with patch.dict(os.environ, env):
            self.assertEqual("https://ghe.example.com/org/repo", detect_repo_web_url(self.tmp))

    def test_detect_should_ignore_invalid_github_variables(self):
        self.init_repo()
        self.write("a.py", "x = 1\n")
        commit_all(self.tmp, ALICE, OLD_DAY)
        env = {"GITHUB_SERVER_URL": "ftp://nope", "GITHUB_REPOSITORY": "org/repo", "GITHUB_SHA": "not-a-sha"}

        with patch.dict(os.environ, env):
            self.assertIsNone(detect_repo_web_url(self.tmp))
            self.assertEqual(run_git(self.tmp, "rev-parse", "HEAD"), detect_commit_sha(self.tmp))


@unittest.skipUnless(GIT_AVAILABLE, "git is not installed")
class TestBlame(GitTestCase):
    def test_blame_file_should_report_author_and_date_per_line(self):
        self.make_two_author_repo()

        blame = blame_file(self.tmp, "a.py", today=TODAY)

        self.assertEqual(BlameLine("Alice Anderson", "alice@example.com", OLD_DAY), blame[1])
        self.assertEqual(BlameLine("Bob Brown", "bob@example.com", RECENT_DAY), blame[2])
        self.assertEqual(BlameLine("Bob Brown", "bob@example.com", RECENT_DAY), blame[3])

    def test_blame_file_should_limit_to_requested_lines(self):
        self.make_two_author_repo()

        blame = blame_file(self.tmp, "a.py", lines=[3, 1, 3], today=TODAY)

        self.assertEqual({1, 3}, set(blame))
        self.assertEqual(OLD_DAY, blame[1].created_date)

    def test_blame_file_should_blame_the_whole_file_for_very_many_lines(self):
        self.make_two_author_repo()

        with patch.object(git_meta, "MAX_BLAME_RANGES", 1):
            blame = blame_file(self.tmp, "a.py", lines=[1, 2], today=TODAY)

        self.assertEqual({1, 2, 3}, set(blame))

    def test_blame_file_should_mark_modified_lines_as_uncommitted(self):
        self.make_two_author_repo()
        self.write("a.py", "# TODO old one\n# TODO recent one\n# TODO brand new\n")

        blame = blame_file(self.tmp, "a.py", today=TODAY)

        self.assertTrue(blame[1].committed)
        self.assertEqual(BlameLine(None, None, TODAY, committed=False), blame[3])

    def test_blame_file_should_return_empty_for_untracked_files_and_empty_repos(self):
        self.init_repo()
        self.write("new.py", "# TODO untracked\n")

        self.assertEqual({}, blame_file(self.tmp, "new.py", today=TODAY))
        self.assertEqual({}, blame_file(self.tmp, "missing.py", today=TODAY))

    def test_blame_file_should_return_empty_if_git_is_missing(self):
        with patch("todonotifier.git_meta.subprocess.run", side_effect=FileNotFoundError):
            self.assertEqual({}, blame_file(self.tmp, "a.py"))

    def test_blame_file_defaults_to_the_current_day_for_uncommitted_lines(self):
        self.make_two_author_repo()
        self.write("a.py", "changed\n")

        self.assertEqual(date.today(), blame_file(self.tmp, "a.py")[1].created_date)

    def test_blame_files_should_blame_each_file_once(self):
        self.make_two_author_repo()
        self.write("b.py", "# TODO b\n")
        commit_all(self.tmp, BOB, RECENT_DAY)

        with patch.object(git_meta, "blame_file", wraps=git_meta.blame_file) as spy:
            result = blame_files(self.tmp, ["a.py", "b.py", "a.py"], max_workers=2, lines_by_file={"b.py": [1]}, today=TODAY)

        self.assertEqual(2, spy.call_count)
        self.assertEqual({"a.py", "b.py"}, set(result))
        self.assertEqual("bob@example.com", result["b.py"][1].author_email)

    def test_blame_files_without_paths_should_not_run_git(self):
        with patch("todonotifier.git_meta.subprocess.run") as run:
            self.assertEqual({}, blame_files(self.tmp, []))

        run.assert_not_called()

    def test_blame_files_should_default_the_reference_day(self):
        self.make_two_author_repo()

        self.assertEqual({"a.py"}, set(blame_files(self.tmp, ["a.py"])))


@unittest.skipUnless(GIT_AVAILABLE, "git is not installed")
class TestEnrichWithGit(GitTestCase):
    def enrich(self, settings: Optional[ScanSettings] = None, **kwargs) -> list:
        settings = settings or ScanSettings(paths=[self.tmp], use_git_blame=True, **kwargs)
        return scan(settings, today=TODAY).items

    def test_should_fill_author_and_created_date_per_todo(self):
        self.make_two_author_repo()

        items = self.enrich()

        self.assertEqual(
            [("Alice Anderson", "git_blame", OLD_DAY), ("Bob Brown", "git_blame", RECENT_DAY), ("carol", "annotation", RECENT_DAY)],
            [(item.author, item.author_source, item.created_date) for item in items],
        )

    def test_annotation_should_always_win_over_blame_and_aliases(self):
        self.make_two_author_repo()

        items = self.enrich(author_aliases={"bob@example.com": "bobby"})

        self.assertEqual("carol", items[2].author)
        self.assertEqual("annotation", items[2].author_source)

    def test_should_apply_aliases_case_insensitively(self):
        self.make_two_author_repo()

        items = self.enrich(author_aliases={"Alice@Example.COM": "ally"})

        self.assertEqual(["ally", "Bob Brown"], [item.author for item in items[:2]])
        self.assertEqual("git_blame", items[0].author_source)

    def test_default_due_days_should_mark_old_items_stale_and_never_overdue(self):
        self.make_two_author_repo()

        items = self.enrich(default_due_days=90)

        old, recent, explicit = items
        self.assertEqual(
            (OLD_DAY + timedelta(days=90), "default", True, False, 10), (old.due_date, old.due_source, old.is_stale, old.is_overdue, old.days_past_due)
        )
        self.assertEqual(
            (RECENT_DAY + timedelta(days=90), "default", False, False, 0),
            (recent.due_date, recent.due_source, recent.is_stale, recent.is_overdue, recent.days_past_due),
        )
        self.assertEqual(date(2030, 1, 1), explicit.due_date)
        self.assertEqual("explicit", explicit.due_source)

    def test_explicit_date_should_win_over_default(self):
        self.init_repo()
        self.write("a.py", "# TODO {2025-01-01} @dave explicit and long gone\n")
        commit_all(self.tmp, ALICE, OLD_DAY)

        (item,) = self.enrich(default_due_days=90)

        self.assertEqual((date(2025, 1, 1), "explicit", True, False), (item.due_date, item.due_source, item.is_overdue, item.is_stale))

    def test_default_due_days_off_values_should_leave_due_source_none(self):
        self.make_two_author_repo()

        for days in (None, 0, -5, True):
            with self.subTest(days=days):
                items = self.enrich(default_due_days=days)
                self.assertEqual(["none", "none", "explicit"], [item.due_source for item in items])
                self.assertEqual([OLD_DAY, RECENT_DAY, RECENT_DAY], [item.created_date for item in items])

    def test_blame_off_should_leave_items_untouched(self):
        self.make_two_author_repo()

        items = self.enrich(ScanSettings(paths=[self.tmp], default_due_days=90))

        self.assertEqual([None, None, None], [item.created_date for item in items])
        self.assertEqual(["none", "none", "explicit"], [item.due_source for item in items])

    def test_uncommitted_and_untracked_lines(self):
        self.make_two_author_repo()
        self.write("a.py", "# TODO old one\n# TODO recent one\n# TODO edited and uncommitted\n")
        self.write("untracked.py", "# TODO never added\n")

        with self.assertLogs(LOGGER_NAME, level="INFO") as logs:
            items = self.enrich(default_due_days=90)

        by_file = {(item.file, item.line): item for item in items}
        edited = by_file[("a.py", 3)]
        untracked = by_file[("untracked.py", 1)]
        for item in (edited, untracked):
            self.assertIsNone(item.author)
            self.assertEqual("unknown", item.author_source)
            self.assertEqual(TODAY, item.created_date)
            self.assertEqual((TODAY + timedelta(days=90), "default", False), (item.due_date, item.due_source, item.is_stale))
        self.assertEqual("Alice Anderson", by_file[("a.py", 1)].author)
        self.assertEqual(1, sum(INFO_UNCOMMITTED.format(count=2) in message for message in logs.output))

    def test_uncommitted_line_with_annotation_should_keep_the_author(self):
        self.init_repo()
        self.write("a.py", "# TODO {2030-01-01} @erin mine\n")

        (item,) = self.enrich()

        self.assertEqual(("erin", "annotation", TODAY), (item.author, item.author_source, item.created_date))

    def test_non_git_directory_should_warn_once_and_skip(self):
        with tempfile.TemporaryDirectory() as outside, patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": os.path.dirname(os.path.realpath(outside))}):
            self.write("a.py", "# TODO plain\n# TODO {2030-01-01} @frank dated\n", base=outside)

            with self.assertLogs(LOGGER_NAME, level="WARNING") as logs:
                items = scan(ScanSettings(paths=[outside], use_git_blame=True, default_due_days=90), today=TODAY).items

        self.assertEqual(1, len(logs.records))
        self.assertIn(WARNING_NOT_A_GIT_REPO.format(path=os.path.realpath(outside)), logs.output[0])
        self.assertEqual(["none", "explicit"], [item.due_source for item in items])
        self.assertEqual([None, None], [item.created_date for item in items])
        self.assertEqual([None, "frank"], [item.author for item in items])

    def test_a_repository_of_another_user_should_say_so_instead_of_claiming_it_is_not_a_repository(self):
        # git refuses repositories owned by another user (Docker bind mounts, container jobs): "fatal: detected dubious ownership"
        self.make_two_author_repo()
        refused = subprocess.CompletedProcess(
            ["git"], 128, stdout=b"", stderr=f"fatal: detected dubious ownership in repository at '{self.tmp}'\n".encode()
        )

        with patch("todonotifier.git_meta._run_git", return_value=refused), self.assertLogs(LOGGER_NAME, level="WARNING") as logs:
            items = self.enrich(default_due_days=90)

        self.assertEqual([WARNING_UNSAFE_REPO.format(path=self.tmp)], [record.getMessage() for record in logs.records])
        self.assertIn(f"git config --global --add safe.directory {self.tmp}", logs.records[0].getMessage())
        self.assertNotIn("not inside a git repository", logs.records[0].getMessage())
        self.assertTrue(all(item.created_date is None for item in items))

    def test_git_missing_should_warn_once_and_not_crash(self):
        self.make_two_author_repo()

        with patch("todonotifier.git_meta.subprocess.run", side_effect=FileNotFoundError), self.assertLogs(LOGGER_NAME, level="WARNING") as logs:
            items = self.enrich(default_due_days=90)

        self.assertEqual([WARNING_GIT_NOT_INSTALLED], [record.getMessage() for record in logs.records])
        self.assertEqual(["none", "none", "explicit"], [item.due_source for item in items])
        self.assertTrue(all(item.created_date is None for item in items))

    def test_shallow_clone_should_warn_once_and_still_run_blame(self):
        self.make_two_author_repo()
        clone = os.path.join(self.tmp, "clones", "shallow")
        os.makedirs(os.path.dirname(clone))
        run_git(self.tmp, "clone", "-q", "--depth", "1", f"file://{self.tmp}", clone)

        with self.assertLogs(LOGGER_NAME, level="WARNING") as logs:
            items = scan(ScanSettings(paths=[clone], use_git_blame=True, default_due_days=90), today=TODAY).items

        self.assertEqual([WARNING_SHALLOW_CLONE], [record.getMessage() for record in logs.records])
        self.assertEqual(3, len(items))
        self.assertTrue(all(item.created_date is not None for item in items))

    def test_full_clone_should_not_warn(self):
        self.make_two_author_repo()

        with self.assertNoLogs(LOGGER_NAME, level="WARNING"):
            self.enrich()

    def test_subdirectory_scan_should_blame_with_repo_relative_paths_and_keep_scan_root_relative_files(self):
        self.init_repo()
        self.write("pkg/sub/a.py", "# TODO nested\n")
        commit_all(self.tmp, ALICE, OLD_DAY)
        run_git(self.tmp, "remote", "add", "origin", "git@example.com:org/repo.git")
        sha = run_git(self.tmp, "rev-parse", "HEAD")

        (item,) = scan(ScanSettings(paths=[os.path.join(self.tmp, "pkg")], use_git_blame=True), today=TODAY).items

        self.assertEqual("sub/a.py", item.file)
        self.assertEqual("Alice Anderson", item.author)
        self.assertEqual(f"https://example.com/org/repo/blob/{sha}/pkg/sub/a.py#L1", item.web_url)

    def test_web_url_should_use_settings_values_before_detection(self):
        self.make_two_author_repo()
        run_git(self.tmp, "remote", "add", "origin", "git@example.com:org/repo.git")
        sha = run_git(self.tmp, "rev-parse", "HEAD")

        explicit = self.enrich(repo_web_url="https://git.corp/team/proj", commit_sha="f" * 40)
        detected_sha_only = self.enrich(repo_web_url="https://git.corp/team/proj")
        detected = self.enrich()

        self.assertEqual(f"https://git.corp/team/proj/blob/{'f' * 40}/a.py#L1", explicit[0].web_url)
        self.assertEqual(f"https://git.corp/team/proj/blob/{sha}/a.py#L2", detected_sha_only[1].web_url)
        self.assertEqual(f"https://example.com/org/repo/blob/{sha}/a.py#L3", detected[2].web_url)

    def test_web_url_should_stay_unset_without_remote(self):
        self.make_two_author_repo()

        self.assertTrue(all(item.web_url is None for item in self.enrich()))

    def test_scanned_files_with_non_ascii_names(self):
        self.init_repo()
        self.write("café/über.py", "# TODO unicode\n")
        commit_all(self.tmp, BOB, RECENT_DAY)

        (item,) = self.enrich()

        self.assertEqual(("Bob Brown", RECENT_DAY), (item.author, item.created_date))

    def test_enrich_with_git_should_do_nothing_without_items(self):
        with patch("todonotifier.git_meta.subprocess.run") as run:
            self.assertEqual([], enrich_with_git([], ScanSettings(use_git_blame=True), self.tmp, TODAY))

        run.assert_not_called()

    def test_enrich_with_git_should_leave_author_unknown_if_blame_has_no_name(self):
        self.make_two_author_repo()
        item = TodoItem(file="a.py", line=1, tag="TODO", message="m")
        nameless = {"a.py": {1: BlameLine(None, None, OLD_DAY)}}

        with patch.object(git_meta, "blame_files", return_value=nameless):
            enrich_with_git([item], ScanSettings(use_git_blame=True), self.tmp, TODAY)

        self.assertEqual((None, "unknown", OLD_DAY), (item.author, item.author_source, item.created_date))


DIFF = """\
diff --git a/src/a.py b/src/a.py
index 1111111..2222222 100644
--- a/src/a.py
+++ b/src/a.py
@@ -3 +3,2 @@ def f():
-old
+new one
+new two
@@ -10,2 +11,0 @@ def g():
-gone 1
-gone 2
@@ -20,0 +20,3 @@
+x
+y
+z
\\ No newline at end of file
diff --git a/src/my file.py b/src/my file.py
index 1111111..2222222 100644
--- a/src/my file.py\t
+++ b/src/my file.py\t
@@ -1 +1 @@
-a
+b
diff --git a/old.py b/new.py
similarity index 90%
rename from old.py
rename to new.py
--- a/old.py
+++ b/new.py
@@ -5 +5 @@
-a
+b
diff --git a/gone.py b/gone.py
deleted file mode 100644
--- a/gone.py
+++ /dev/null
@@ -1,2 +0,0 @@
-a
-b
diff --git "a/caf\\303\\251.py" "b/caf\\303\\251.py"
--- "a/caf\\303\\251.py"
+++ "b/caf\\303\\251.py"
@@ -1,0 +2 @@
+added
diff --git a/tricky.py b/tricky.py
--- a/tricky.py
+++ b/tricky.py
@@ -1 +1 @@
-x
+++ b/not-a-header
diff --git a/img.png b/img.png
Binary files a/img.png and b/img.png differ
"""


class TestParseChangedLines(unittest.TestCase):
    def test_should_collect_added_and_changed_lines_per_file(self):
        changed = parse_changed_lines(DIFF)

        self.assertEqual({3, 4, 20, 21, 22}, changed["src/a.py"])
        self.assertEqual({1}, changed["src/my file.py"])
        self.assertEqual({5}, changed["new.py"])
        self.assertEqual({2}, changed["café.py"])

    def test_should_not_mistake_an_added_line_that_looks_like_a_header_for_a_file(self):
        changed = parse_changed_lines(DIFF)

        self.assertEqual({1}, changed["tricky.py"])
        self.assertNotIn("not-a-header", changed)

    def test_should_ignore_deleted_files_pure_deletions_and_binary_files(self):
        changed = parse_changed_lines(DIFF)

        self.assertNotIn("gone.py", changed)
        self.assertNotIn("old.py", changed)
        self.assertNotIn("img.png", changed)
        self.assertEqual({"src/a.py", "src/my file.py", "new.py", "café.py", "tricky.py"}, set(changed))

    def test_should_return_nothing_for_an_empty_diff(self):
        self.assertEqual({}, parse_changed_lines(""))

    def test_unquote_diff_path(self):
        cases = {
            "plain.py": "plain.py",
            '"a\\tb"': "a\tb",
            '"caf\\303\\251"': "café",
            '"say \\"hi\\""': 'say "hi"',
            '"back\\\\slash"': "back\\slash",
            '"bad\\9escape"': "bad\\9escape",
            '"ends\\"': "ends\\",
            '"': '"',
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(expected, _unquote_diff_path(raw))


class TestToRepoPath(unittest.TestCase):
    def test_should_make_scan_root_relative_paths_repo_relative(self):
        self.assertEqual("src/pkg/a.py", to_repo_path("pkg/a.py", "/repo/src", "/repo"))
        self.assertEqual("a.py", to_repo_path("a.py", "/repo", "/repo"))
        self.assertEqual("../outside/a.py", to_repo_path("a.py", "/outside", "/repo"))


@unittest.skipUnless(GIT_AVAILABLE, "git is not installed")
class TestChangedLines(GitTestCase):
    def make_repo(self) -> None:
        self.init_repo()
        self.write("a.py", "one\ntwo\nthree\nfour\n")
        self.write("old name.py", "".join(f"line {number}\n" for number in range(1, 21)))
        self.write("gone.py", "bye\n")
        self.write("keep.py", "same\n")
        commit_all(self.tmp, ALICE, OLD_DAY)

    def test_should_report_changed_lines_of_modified_files(self):
        self.make_repo()
        self.write("a.py", "one\nTWO\nthree\nnew\nfour\n")
        commit_all(self.tmp, BOB, RECENT_DAY)
        self.write("a.py", "one\nTWO\nthree\nnew\nfour\nlast")  # Not committed: working tree against the ref

        self.assertEqual({"a.py": {2, 4, 6}}, changed_lines(self.tmp, "HEAD~1"))
        self.assertEqual({"a.py": {6}}, changed_lines(self.tmp, "HEAD"))

    def test_should_follow_renames_and_skip_deletions(self):
        self.make_repo()
        os.remove(os.path.join(self.tmp, "gone.py"))
        os.rename(os.path.join(self.tmp, "old name.py"), os.path.join(self.tmp, "new name.py"))
        self.write("new name.py", "".join(f"line {number}\n" if number != 7 else "changed\n" for number in range(1, 21)))
        run_git(self.tmp, "add", "-A")

        self.assertEqual({"new name.py": {7}}, changed_lines(self.tmp, "HEAD"))

    def test_should_count_untracked_files_as_fully_changed_but_not_ignored_ones(self):
        self.make_repo()
        self.write(".gitignore", "ignored.py\n")
        self.write("ignored.py", "# TODO ignored\n")
        self.write("fresh.py", "a\nb\nc")  # No trailing newline
        self.write("empty.py", "")
        self.write("sub dir/inner.py", "x\n")
        nested = self.init_repo(os.path.join(self.tmp, "nested"))
        self.write("n.py", "x\n", base=nested)

        changed = changed_lines(self.tmp, "HEAD")

        self.assertEqual({".gitignore": {1}, "fresh.py": {1, 2, 3}, "sub dir/inner.py": {1}}, changed)

    def test_should_handle_non_ascii_names(self):
        self.make_repo()
        self.write("café.py", "# TODO\n")
        commit_all(self.tmp, ALICE, RECENT_DAY)
        self.write("café.py", "# TODO\n# TODO again\n")

        self.assertEqual({"café.py": {2}}, changed_lines(self.tmp, "HEAD"))

    def test_should_be_independent_of_diff_prefix_config(self):
        self.make_repo()
        run_git(self.tmp, "config", "diff.noprefix", "true")
        self.write("a.py", "one\nTWO\nthree\nfour\n")

        self.assertEqual({"a.py": {2}}, changed_lines(self.tmp, "HEAD"))

    def test_unknown_ref_should_raise_a_helpful_error(self):
        self.make_repo()

        with self.assertRaises(GitError) as context:
            changed_lines(self.tmp, "no-such-branch")

        self.assertIn("Unknown git ref 'no-such-branch'", str(context.exception))
        self.assertIn("fetch-depth", str(context.exception))

    def test_ref_that_looks_like_an_option_should_be_rejected(self):
        self.make_repo()

        for ref in ("--output=/tmp/evil", "-p", ""):
            with self.subTest(ref=ref), self.assertRaises(GitError):
                changed_lines(self.tmp, ref)
        self.assertFalse(os.path.exists("/tmp/evil"))

    def test_should_raise_if_git_is_missing_or_fails(self):
        self.make_repo()

        with patch("todonotifier.git_meta.subprocess.run", side_effect=FileNotFoundError), self.assertRaises(GitError) as context:
            changed_lines(self.tmp, "HEAD")
        self.assertIn("git executable", str(context.exception))

        failed = subprocess.CompletedProcess(["git"], 128, stdout=b"", stderr=b"fatal")
        ok = subprocess.CompletedProcess(["git"], 0, stdout=b"", stderr=b"")
        for responses in ([ok, failed], [ok, ok, failed], [ok, None]):
            with self.subTest(responses=len(responses)), patch("todonotifier.git_meta._run_git", side_effect=responses), self.assertRaises(GitError):
                changed_lines(self.tmp, "HEAD")


@unittest.skipUnless(GIT_AVAILABLE, "git is not installed")
class TestFilterGitListed(GitTestCase):
    def make_repo(self) -> None:
        self.init_repo()
        self.write(".gitignore", "ignored*.py\n")
        self.write("tracked.py", "x = 1\n")
        self.write("src/inner.py", "x = 1\n")
        run_git(self.tmp, "add", "-A")
        self.write("untracked.py", "x = 1\n")
        self.write("ignored1.py", "x = 1\n")
        self.write("a[1].py", "x = 1\n")  # A glob character: must match literally

    def paths(self, *names: str) -> list:
        return [os.path.join(self.tmp, *name.split("/")) for name in names]

    def test_should_keep_listed_files_in_order_and_drop_ignored_ones(self):
        self.make_repo()
        given = self.paths("untracked.py", "ignored1.py", "src/inner.py", "tracked.py", "a[1].py")

        self.assertEqual(self.paths("untracked.py", "src/inner.py", "tracked.py", "a[1].py"), filter_git_listed(given))

    def test_should_run_one_ls_files_call_for_many_files(self):
        self.make_repo()
        given = self.paths("untracked.py", "ignored1.py", "src/inner.py", "tracked.py")
        real_run = subprocess.run
        calls = []

        def spy(command, *args, **kwargs):
            calls.append(command)
            return real_run(command, *args, **kwargs)

        with patch("todonotifier.git_meta.subprocess.run", side_effect=spy):
            filter_git_listed(given)

        self.assertEqual(1, sum(1 for command in calls if "ls-files" in command))
        self.assertEqual(2, len(calls))  # rev-parse and ls-files

    def test_should_split_very_long_lists_into_several_calls_with_the_same_result(self):
        self.make_repo()
        given = self.paths("untracked.py", "ignored1.py", "src/inner.py", "tracked.py")

        with patch.object(git_meta, "MAX_PATHSPEC_CHARS", 30):
            self.assertEqual(self.paths("untracked.py", "src/inner.py", "tracked.py"), filter_git_listed(given))

    def test_should_return_empty_for_no_files(self):
        self.assertEqual([], filter_git_listed([]))

    def test_should_return_none_outside_a_repository_or_if_git_fails(self):
        self.make_repo()
        with tempfile.TemporaryDirectory() as outside:
            self.assertIsNone(filter_git_listed([os.path.join(outside, "a.py")]))

        failed = subprocess.CompletedProcess(["git"], 128, stdout=b"", stderr=b"fatal")
        root_ok = subprocess.CompletedProcess(["git"], 0, stdout=self.tmp.encode(), stderr=b"")
        for second in (None, failed):
            with patch("todonotifier.git_meta._run_git", side_effect=[root_ok, second]):
                self.assertIsNone(filter_git_listed(self.paths("tracked.py")))

    def test_paths_from_git_should_use_the_separators_of_the_platform(self):
        # git prints "/" everywhere. On Windows the paths of the caller have backslashes, so without normalising none of them matched and
        # `todonotifier scan file.py` (the pre-commit way) saw no file at all
        with patch.object(os.path, "join", ntpath.join), patch.object(os.path, "normpath", ntpath.normpath), patch.object(os.path, "isfile", return_value=True):
            decoded = _decode_paths(b"src/inner.py\0top.py\0", "C:\\repo")

        self.assertEqual(["C:\\repo\\src\\inner.py", "C:\\repo\\top.py"], decoded)

    def test_should_match_named_files_whatever_the_case_and_separators_of_the_platform(self):
        self.make_repo()
        given = self.paths("src/inner.py", "tracked.py")

        with patch.object(os.path, "normcase", lambda path: path.upper()):
            self.assertEqual(given, filter_git_listed(given))

    def test_should_return_none_for_paths_without_a_common_directory(self):
        with patch("todonotifier.git_meta.os.path.commonpath", side_effect=ValueError):
            self.assertIsNone(filter_git_listed(["/a/x.py", "/b/y.py"]))


if __name__ == "__main__":
    unittest.main()
