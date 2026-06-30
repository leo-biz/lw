from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.task_commit_report import audit, commits_for_task, cumulative_diff, resolve_task_id


class TaskCommitReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(("git", "init", "-q", str(self.root)), check=True)
        subprocess.run(("git", "-C", str(self.root), "config", "user.email", "test@example.com"), check=True)
        subprocess.run(("git", "-C", str(self.root), "config", "user.name", "Test"), check=True)
        self.work = self.root / "work"
        self.aliases = self.root / "config" / "task-commit-aliases.yaml"
        self.make_task("task-canonical")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def make_task(self, task_id: str) -> None:
        path = self.work / "ready" / f"{task_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\nid: {task_id}\n---\n")

    def commit(self, subject: str, task_id: str = "") -> None:
        sample = self.root / "sample.txt"
        sample.write_text(sample.read_text() + subject + "\n" if sample.exists() else subject + "\n")
        subprocess.run(("git", "-C", str(self.root), "add", "sample.txt"), check=True)
        command = ["git", "-C", str(self.root), "commit", "-q", "-m", subject]
        if task_id:
            command.extend(("-m", f"Task: {task_id}", "-m", "Commit-Type: checkpoint"))
        subprocess.run(command, check=True)

    def test_resolves_only_reviewed_alias(self) -> None:
        self.aliases.parent.mkdir()
        self.aliases.write_text(
            "aliases:\n"
            "  task-reviewed:\n"
            "    canonical_task: task-canonical\n"
            "    reviewed: true\n"
            "  task-unreviewed:\n"
            "    canonical_task: task-canonical\n"
            "    reviewed: false\n"
        )
        self.assertEqual(resolve_task_id("task-reviewed", self.work, self.aliases), "task-canonical")
        with self.assertRaisesRegex(ValueError, "does not resolve"):
            resolve_task_id("task-unreviewed", self.work, self.aliases)

    def test_reports_canonical_and_legacy_alias_commits(self) -> None:
        self.aliases.parent.mkdir()
        self.aliases.write_text("aliases:\n  task-legacy:\n    canonical_task: task-canonical\n    reviewed: true\n")
        self.commit("legacy change", "task-legacy")
        self.commit("canonical change", "task-canonical")

        payload = commits_for_task("task-canonical", self.root, self.work, self.aliases)

        self.assertEqual([item["subject"] for item in payload["commits"]], ["canonical change", "legacy change"])
        self.assertEqual(payload["aliases"], ["task-legacy"])

    def test_cumulative_diff_includes_all_attributed_changes(self) -> None:
        self.commit("first", "task-canonical")
        self.commit("second", "task-canonical")

        payload = cumulative_diff("task-canonical", self.root, self.work, self.aliases)

        self.assertIn("+first", payload)
        self.assertIn("+second", payload)

    def test_audit_reports_orphans_and_unattributed_commits(self) -> None:
        self.commit("unattributed")
        self.commit("orphan", "task-missing")

        payload = audit(self.root, self.work, self.aliases)

        self.assertEqual([item["subject"] for item in payload["orphan_task_trailers"]], ["orphan"])
        self.assertEqual([item["subject"] for item in payload["unattributed_commits"]], ["unattributed"])
        self.assertEqual(payload["heuristic_suggestions"], [])


if __name__ == "__main__":
    unittest.main()
