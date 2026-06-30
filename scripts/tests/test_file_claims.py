from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

from scripts.file_claims import claim_paths, git_status_tag, normalize_path, release_paths, show_status


class FileClaimsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.ledger = self.root / "work" / ".file-claims.json"
        self.lock = self.root / "work" / ".file-claims.lock"
        (self.root / "work").mkdir()
        subprocess.run(("git", "init", "-q", str(self.root)), check=True)
        (self.root / "shared.md").write_text("clean\n")
        subprocess.run(("git", "-C", str(self.root), "add", "shared.md"), check=True)
        subprocess.run(
            ("git", "-C", str(self.root), "commit", "-qm", "initial"),
            check=True,
            env={
                "PATH": "/usr/bin:/bin",
                "GIT_AUTHOR_NAME": "Test",
                "GIT_AUTHOR_EMAIL": "test@example.com",
                "GIT_COMMITTER_NAME": "Test",
                "GIT_COMMITTER_EMAIL": "test@example.com",
            },
        )
        self.now = datetime(2026, 5, 31, 12, 0, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def claim_args(self, session_id: str, paths: list[str]) -> Namespace:
        return Namespace(
            root=self.root,
            ledger=self.ledger,
            lock=self.lock,
            now=self.now,
            paths=paths,
            agent="codex",
            provider="openai",
            session_id=session_id,
            session_url="",
            task_id="task-example",
            minutes=120,
            allow_shared=False,
        )

    def test_status_marks_owned_and_unclaimed_dirty_files(self) -> None:
        claim_paths(self.claim_args("thread-1", ["shared.md"]))
        (self.root / "shared.md").write_text("changed\n")
        (self.root / "new.md").write_text("new\n")

        output = StringIO()
        with redirect_stdout(output):
            show_status(
                Namespace(root=self.root, ledger=self.ledger, now=self.now)
            )

        self.assertIn("shared.md | OWNED | codex@openai:thread-1 task=task-example", output.getvalue())
        self.assertIn("new.md | UNCLAIMED", output.getvalue())

    def test_overlap_requires_explicit_shared_claim(self) -> None:
        claim_paths(self.claim_args("thread-1", ["wiki"]))
        with self.assertRaisesRegex(ValueError, "overlaps active claim"):
            claim_paths(self.claim_args("thread-2", ["wiki/page.md"]))

    def test_release_removes_session_claim(self) -> None:
        claim_paths(self.claim_args("thread-1", ["shared.md"]))
        release_paths(
            Namespace(
                root=self.root,
                ledger=self.ledger,
                lock=self.lock,
                session_id="thread-1",
                paths=[],
            )
        )
        self.assertEqual(self.ledger.read_text(), "[]\n")

    def test_status_uses_readable_git_tags(self) -> None:
        claim_paths(self.claim_args("thread-1", ["shared.md"]))
        (self.root / "shared.md").write_text("changed\n")
        (self.root / "new.md").write_text("new\n")
        output = StringIO()
        with redirect_stdout(output):
            show_status(Namespace(root=self.root, ledger=self.ledger, now=self.now))
        text = output.getvalue()
        self.assertIn("[MODIFIED]", text)
        self.assertIn("[NEW]", text)
        self.assertNotIn(" M ", text)
        self.assertNotIn("??", text)

    def test_status_unclaimed_includes_full_claim_command(self) -> None:
        (self.root / "new.md").write_text("new\n")
        output = StringIO()
        with redirect_stdout(output):
            show_status(Namespace(root=self.root, ledger=self.ledger, now=self.now))
        text = output.getvalue()
        self.assertIn("new.md | UNCLAIMED", text)
        self.assertNotIn("...", text)
        self.assertIn("scripts/file_claims.py claim new.md", text)

    def test_status_deleted_file_tagged_deleted(self) -> None:
        (self.root / "shared.md").unlink()
        output = StringIO()
        with redirect_stdout(output):
            show_status(Namespace(root=self.root, ledger=self.ledger, now=self.now))
        text = output.getvalue()
        self.assertIn("[DELETED]", text)

    def test_status_json_flag_returns_array(self) -> None:
        (self.root / "new.md").write_text("new\n")
        output = StringIO()
        with redirect_stdout(output):
            show_status(Namespace(root=self.root, ledger=self.ledger, now=self.now, json=True))
        data = json.loads(output.getvalue())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["label"], "UNCLAIMED")
        self.assertEqual(data[0]["path"], "new.md")

    def test_git_status_tag_maps_codes(self) -> None:
        self.assertEqual(git_status_tag("??"), "[NEW]")
        self.assertEqual(git_status_tag(" D"), "[DELETED]")
        self.assertEqual(git_status_tag("D "), "[DELETED]")
        self.assertEqual(git_status_tag(" M"), "[MODIFIED]")
        self.assertEqual(git_status_tag("R "), "[RENAMED]")
        self.assertEqual(git_status_tag("A "), "[ADDED]")

    def test_normalize_path_preserves_dotfile_name(self) -> None:
        self.assertEqual(normalize_path(self.root, ".gitignore"), ".gitignore")


if __name__ == "__main__":
    unittest.main()
