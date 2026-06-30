from __future__ import annotations

import subprocess
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from scripts.agent_commit import create_commit


class AgentCommitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(("git", "init", "-q", str(self.root)), check=True)
        subprocess.run(("git", "-C", str(self.root), "config", "user.email", "test@example.com"), check=True)
        subprocess.run(("git", "-C", str(self.root), "config", "user.name", "Test"), check=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def args(self) -> Namespace:
        return Namespace(
            root=self.root,
            commit_type="checkpoint",
            message="Checkpoint example",
            agent="codex",
            provider="openai",
            session_id="thread-123",
            session_url="",
            task_id="task-example",
            paths=[],
            allow_non_task_attribution=True,
        )

    def test_commit_adds_searchable_attribution_trailers(self) -> None:
        (self.root / "example.md").write_text("hello\n")
        subprocess.run(("git", "-C", str(self.root), "add", "example.md"), check=True)

        create_commit(self.args())

        body = subprocess.run(
            ("git", "-C", str(self.root), "log", "-1", "--pretty=format:%B"),
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertIn("Agent: codex", body)
        self.assertIn("Provider: openai", body)
        self.assertIn("Session: thread-123", body)
        self.assertIn("Task: task-example", body)
        self.assertIn("Commit-Type: checkpoint", body)

    def test_commit_requires_explicitly_staged_files(self) -> None:
        with self.assertRaisesRegex(ValueError, "no staged files"):
            create_commit(self.args())

    def test_commit_rejects_task_id_without_ledger_file(self) -> None:
        (self.root / "example.md").write_text("hello\n")
        subprocess.run(("git", "-C", str(self.root), "add", "example.md"), check=True)
        args = self.args()
        args.allow_non_task_attribution = False

        with self.assertRaisesRegex(ValueError, "does not resolve to a ledger file"):
            create_commit(args)

    def test_commit_accepts_task_id_with_ledger_file(self) -> None:
        task = self.root / "work" / "ready" / "example.md"
        task.parent.mkdir(parents=True)
        task.write_text("---\nid: task-example\n---\n")
        (self.root / "example.md").write_text("hello\n")
        subprocess.run(("git", "-C", str(self.root), "add", "example.md"), check=True)
        args = self.args()
        args.allow_non_task_attribution = False

        create_commit(args)

    def test_path_scope_preserves_unrelated_staged_file(self) -> None:
        (self.root / "intended.md").write_text("intended\n")
        (self.root / "other.md").write_text("other\n")
        subprocess.run(("git", "-C", str(self.root), "add", "intended.md", "other.md"), check=True)
        args = self.args()
        args.paths = ["intended.md"]

        create_commit(args)

        committed = subprocess.run(
            ("git", "-C", str(self.root), "show", "--pretty=format:", "--name-only", "HEAD"),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        staged = subprocess.run(
            ("git", "-C", str(self.root), "diff", "--cached", "--name-only"),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        self.assertEqual(committed, ["intended.md"])
        self.assertEqual(staged, ["other.md"])

    def test_path_scope_rejects_unstaged_changes(self) -> None:
        (self.root / "example.md").write_text("one\n")
        subprocess.run(("git", "-C", str(self.root), "add", "example.md"), check=True)
        (self.root / "example.md").write_text("two\n")
        args = self.args()
        args.paths = ["example.md"]

        with self.assertRaisesRegex(ValueError, "unstaged changes"):
            create_commit(args)

    def test_path_scope_commits_both_sides_of_rename(self) -> None:
        (self.root / "old.md").write_text("task\n")
        subprocess.run(("git", "-C", str(self.root), "add", "old.md"), check=True)
        subprocess.run(("git", "-C", str(self.root), "commit", "-m", "seed"), check=True, capture_output=True)
        (self.root / "old.md").rename(self.root / "new.md")
        subprocess.run(("git", "-C", str(self.root), "add", "old.md", "new.md"), check=True)
        args = self.args()
        args.paths = ["old.md", "new.md"]

        create_commit(args)

        staged = subprocess.run(
            ("git", "-C", str(self.root), "diff", "--cached", "--name-only"),
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertEqual(staged, "")
        self.assertFalse((self.root / "old.md").exists())
        self.assertTrue((self.root / "new.md").exists())

    @patch("scripts.agent_commit.update_presence_best_effort")
    def test_checkpoint_commit_updates_presence(self, update_presence) -> None:
        (self.root / "example.md").write_text("hello\n")
        subprocess.run(("git", "-C", str(self.root), "add", "example.md"), check=True)

        create_commit(self.args())

        update_presence.assert_called_once()
        action, = update_presence.call_args.args
        self.assertEqual(action, "checkpoint")
        self.assertEqual(update_presence.call_args.kwargs["session_id"], "thread-123")
        self.assertEqual(update_presence.call_args.kwargs["task_id"], "task-example")
        self.assertTrue(update_presence.call_args.kwargs["last_commit"])

    @patch("scripts.agent_commit.update_presence_best_effort")
    def test_complete_commit_ends_presence(self, update_presence) -> None:
        (self.root / "example.md").write_text("hello\n")
        subprocess.run(("git", "-C", str(self.root), "add", "example.md"), check=True)
        args = self.args()
        args.commit_type = "complete"

        create_commit(args)

        update_presence.assert_called_once()
        action, = update_presence.call_args.args
        self.assertEqual(action, "end")


if __name__ == "__main__":
    unittest.main()
