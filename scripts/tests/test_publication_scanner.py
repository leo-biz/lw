"""
test_publication_scanner.py — Unit tests for publication_scanner.py.

All fixtures are synthetic and contain no real secrets, paths, or
Slack identifiers.  Strings that look like secrets are intentionally
malformed so they do not represent real credentials.

Run:
    python3 -m unittest scripts.tests.test_publication_scanner -v
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Allow running from vault root or from within scripts/tests/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.publication_scanner import (  # noqa: E402
    Finding,
    format_report,
    main,
    scan_file,
    scan_path,
    scan_text,
    _load_allowlist,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _findings_for(text: str, path: Path | None = None) -> list[Finding]:
    """Return findings for *text* with no allowlist."""
    return scan_text(text, path or Path("test_fixture.md"))


def _categories(findings: list[Finding]) -> list[str]:
    return [f.category for f in findings]


# ---------------------------------------------------------------------------
# Secret pattern tests
# ---------------------------------------------------------------------------


class TestSecretPatterns(unittest.TestCase):

    def test_detects_generic_api_key_assignment(self):
        line = "api_key = EXAMPLEKEY1234567890ABCDEF"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertTrue(any("secret:generic-token" in c for c in cats), cats)

    def test_detects_openai_key_prefix(self):
        # Synthetic: sk- followed by enough chars. Not a real key.
        line = "export OPENAI_KEY=sk-FAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKE"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("secret:openai-key", cats, cats)

    def test_detects_anthropic_key_prefix(self):
        line = "ANTHROPIC_KEY=sk-ant-FAKEANTHROPICKEYABCDEFGHIJKLMNOP"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("secret:anthropic-key", cats, cats)

    def test_detects_aws_access_key(self):
        line = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("secret:aws-access-key", cats, cats)

    def test_detects_slack_bot_token(self):
        line = "SLACK_TOKEN=" + "xox" + "b-111111111111-AAAAAAAAAAAAAAAAAAAAAAAA"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("secret:slack-bot-token", cats, cats)

    def test_detects_slack_user_token(self):
        line = "token: " + "xox" + "p-222222222222-BBBBBBBBBBBBBBBBBBBBBBBB"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("secret:slack-user-token", cats, cats)

    def test_detects_github_pat(self):
        line = "GH_TOKEN=" + "ghp" + "_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("secret:github-pat", cats, cats)

    def test_detects_google_api_key(self):
        # AIza + exactly 35 alphanumeric chars = 39 total (real Google API key length)
        line = "GOOGLE_KEY=AIzaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("secret:google-api-key", cats, cats)

    def test_detects_private_key_block(self):
        line = "-----BEGIN RSA PRIVATE KEY-----"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("secret:private-key-block", cats, cats)

    def test_clean_short_string_not_flagged(self):
        # A short key= value should NOT trigger generic token detection
        line = "api_key = short"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertNotIn("secret:generic-token-assignment", cats, cats)

    def test_detects_bearer_token(self):
        line = "Authorization: Bearer FAKEBEARERTOKENFAKEFAKEFAKEFAKE12345"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("secret:bearer-token", cats, cats)


# ---------------------------------------------------------------------------
# Slack ID pattern tests
# ---------------------------------------------------------------------------


class TestSlackIDPatterns(unittest.TestCase):

    def test_detects_slack_workspace_id(self):
        line = "workspace_id: T01ABCDEFGH"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("slack:workspace-id", cats, cats)

    def test_detects_slack_channel_id(self):
        line = "channel: C02XYZABCDE"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("slack:channel-id", cats, cats)

    def test_detects_slack_user_id(self):
        line = "user: U03GHIJKLMN"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("slack:user-id", cats, cats)


# ---------------------------------------------------------------------------
# Local path pattern tests
# ---------------------------------------------------------------------------


class TestLocalPathPatterns(unittest.TestCase):

    def test_detects_macos_user_path(self):
        line = "config_path = /Users/sirleo/Documents/project"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("path:local-users", cats, cats)

    def test_detects_linux_home_path(self):
        line = "HOME=/home/agent/.config"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("path:local-home", cats, cats)

    def test_detects_tilde_home_config(self):
        line = "config: ~/.config/myapp/settings.yaml"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("path:tilde-home", cats, cats)

    def test_clean_relative_path_not_flagged(self):
        line = "config: config/settings.yaml"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertNotIn("path:local-users", cats, cats)
        self.assertNotIn("path:local-home", cats, cats)


# ---------------------------------------------------------------------------
# Audience frontmatter tests
# ---------------------------------------------------------------------------


class TestAudienceFrontmatter(unittest.TestCase):

    def test_detects_private_audience(self):
        text = "---\ntitle: My Doc\naudience: private\n---\n\nContent."
        findings = _findings_for(text)
        cats = _categories(findings)
        self.assertIn("frontmatter:private-audience", cats, cats)

    def test_detects_internal_audience(self):
        text = "---\ntitle: My Doc\naudience: internal\n---\n\nContent."
        findings = _findings_for(text)
        cats = _categories(findings)
        self.assertIn("frontmatter:private-audience", cats, cats)

    def test_public_audience_not_flagged(self):
        text = "---\ntitle: My Doc\naudience: public\n---\n\nContent."
        findings = _findings_for(text)
        cats = _categories(findings)
        self.assertNotIn("frontmatter:private-audience", cats, cats)

    def test_no_audience_not_flagged(self):
        text = "---\ntitle: My Doc\n---\n\nContent."
        findings = _findings_for(text)
        cats = _categories(findings)
        self.assertNotIn("frontmatter:private-audience", cats, cats)


# ---------------------------------------------------------------------------
# Private folder reference tests
# ---------------------------------------------------------------------------


class TestPrivateFolderPatterns(unittest.TestCase):

    def test_detects_raw_folder_reference(self):
        line = "See raw/source-2026-01-01.md for context."
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("path:raw-folder", cats, cats)

    def test_detects_inbox_folder_reference(self):
        line = "Stored in inbox/my-note.md."
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("path:raw-folder", cats, cats)

    def test_detects_private_folder_reference(self):
        line = "Refer to private/config."
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("path:raw-folder", cats, cats)

    def test_detects_client_facing_export(self):
        line = "Output goes to exports/client-facing/report.pdf"
        findings = _findings_for(line)
        cats = _categories(findings)
        self.assertIn("path:client-facing-export", cats, cats)


# ---------------------------------------------------------------------------
# Allowlist tests
# ---------------------------------------------------------------------------


class TestAllowlist(unittest.TestCase):

    def test_allowlisted_match_suppressed(self):
        """A finding whose matched_text is in the allowlist is suppressed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "allowlist.txt"
            # The matched text for the AWS key pattern is the key itself
            f.write_text("AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
            allowlist = _load_allowlist(f)
            line = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
            raw = scan_text(line, Path("fixture.md"))
            filtered = [x for x in raw if not x.is_allowlisted(allowlist)]
            # The AWS key finding should be gone; others may remain
            aws_findings = [x for x in filtered if x.category == "secret:aws-access-key"]
            self.assertEqual(aws_findings, [])

    def test_non_allowlisted_match_retained(self):
        allowlist: set[str] = {"some_other_value"}
        line = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
        raw = scan_text(line, Path("fixture.md"))
        filtered = [x for x in raw if not x.is_allowlisted(allowlist)]
        aws_findings = [x for x in filtered if x.category == "secret:aws-access-key"]
        self.assertTrue(len(aws_findings) > 0)

    def test_allowlist_comment_lines_ignored(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "allowlist.txt"
            f.write_text("# this is a comment\nAKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
            allowlist = _load_allowlist(f)
            self.assertNotIn("# this is a comment", allowlist)
            self.assertIn("AKIAIOSFODNN7EXAMPLE", allowlist)

    def test_missing_allowlist_returns_empty_set(self):
        allowlist = _load_allowlist(Path("/nonexistent/allowlist.txt"))
        self.assertEqual(allowlist, set())


# ---------------------------------------------------------------------------
# scan_file / scan_path integration tests
# ---------------------------------------------------------------------------


class TestScanFileAndPath(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _write(self, name: str, content: str) -> Path:
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def test_scan_file_clean_returns_empty(self):
        p = self._write("clean.md", "# Hello\n\nThis is safe content.\n")
        findings = scan_file(p, set())
        self.assertEqual(findings, [])

    def test_scan_file_with_secret_returns_finding(self):
        p = self._write("secret.md", "api_key = FAKEFAKEFAKEFAKE12345678901234\n")
        findings = scan_file(p, set())
        self.assertTrue(len(findings) > 0)

    def test_scan_path_directory_recurses(self):
        self._write("subdir/clean.md", "# Clean\n")
        self._write("subdir/dirty.py", "token = 'sk-FAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKE'\n")
        findings = scan_path(self.root, set())
        # The dirty.py file should have findings
        files_with_findings = {f.file.name for f in findings}
        self.assertIn("dirty.py", files_with_findings)
        self.assertNotIn("clean.md", files_with_findings)

    def test_scan_path_skips_git_directory(self):
        self._write(".git/config", "api_key = FAKEFAKEFAKEFAKE12345678901234\n")
        findings = scan_path(self.root, set())
        git_findings = [f for f in findings if ".git" in str(f.file)]
        self.assertEqual(git_findings, [])

    def test_scan_path_file_target(self):
        p = self._write("single.md", "/Users/testuser/project/foo.py\n")
        findings = scan_path(p, set())
        cats = _categories(findings)
        self.assertIn("path:local-users", cats, cats)


# ---------------------------------------------------------------------------
# format_report tests
# ---------------------------------------------------------------------------


class TestFormatReport(unittest.TestCase):

    def test_clean_report_says_clean(self):
        report = format_report([])
        self.assertIn("CLEAN", report)

    def test_report_includes_file_and_category(self):
        f = Finding(
            file=Path("exports/test.md"),
            line_no=5,
            category="secret:openai-key",
            matched_text="sk-FAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKE",
        )
        report = format_report([f])
        self.assertIn("exports/test.md", report)
        self.assertIn("secret:openai-key", report)

    def test_report_shows_finding_count(self):
        findings = [
            Finding(Path("a.md"), 1, "secret:openai-key", "sk-FAKEFAKEFAKE12345678901234"),
            Finding(Path("b.md"), 2, "path:local-users", "/Users/test/"),
        ]
        report = format_report(findings)
        self.assertIn("2 finding(s)", report)


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------


class TestCLI(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _write(self, name: str, content: str) -> Path:
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def test_cli_clean_exits_zero(self):
        self._write("clean.md", "# Safe document\n\nNo secrets here.\n")
        code = main([str(self.root)])
        self.assertEqual(code, 0)

    def test_cli_dirty_exits_zero_without_strict(self):
        self._write("dirty.md", "api_key = FAKEFAKEFAKEFAKE12345678901234\n")
        code = main([str(self.root)])
        self.assertEqual(code, 0)  # no --strict => always 0 on findings

    def test_cli_dirty_exits_one_with_strict(self):
        self._write("dirty.md", "api_key = FAKEFAKEFAKEFAKE12345678901234\n")
        code = main([str(self.root), "--strict"])
        self.assertEqual(code, 1)

    def test_cli_nonexistent_path_exits_two(self):
        code = main(["/nonexistent/path/does-not-exist"])
        self.assertEqual(code, 2)

    def test_cli_with_allowlist(self):
        self._write("dirty.md", "AKIAIOSFODNN7EXAMPLE\n")
        al = self._write("allowlist.txt", "AKIAIOSFODNN7EXAMPLE\n")
        code = main([str(self.root), "--allowlist", str(al), "--strict"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
