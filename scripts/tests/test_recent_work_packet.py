from __future__ import annotations

import subprocess
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

import yaml

from scripts.recent_work_packet import build_packet


def task_text(title: str, status: str, checkpoint: str = "") -> str:
    metadata = {
        "title": title,
        "status": status,
        "agent": "test-agent",
        "handoff_checkpoint": checkpoint,
    }
    frontmatter = yaml.safe_dump(metadata, sort_keys=False).rstrip()
    return (
        f"---\n{frontmatter}\n---\n\n"
        "## Activity\n\n"
        "- 2026-05-31 09:00 | test-agent | First activity.\n"
        "- 2026-05-31 09:05 | test-agent | Latest activity.\n"
    )


class RecentWorkPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        subprocess.run(("git", "init", "-q", str(self.root)), check=True)
        subprocess.run(("git", "-C", str(self.root), "config", "user.email", "test@example.com"), check=True)
        subprocess.run(("git", "-C", str(self.root), "config", "user.name", "Test"), check=True)
        for folder in ("in-progress", "review", "blocked", "done"):
            (self.root / "work" / folder).mkdir(parents=True)
        (self.root / "README.md").write_text("tracked\n")
        subprocess.run(("git", "-C", str(self.root), "add", "README.md"), check=True)
        subprocess.run(("git", "-C", str(self.root), "commit", "-qm", "Initial commit"), check=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def args(self) -> Namespace:
        return Namespace(
            root=self.root,
            since="30 days ago",
            max_commits=4,
            max_done=3,
            activity_lines=1,
        )

    def test_reports_dirty_files_commits_active_checkpoint_and_recent_activity(self) -> None:
        (self.root / "dirty.txt").write_text("untracked\n")
        task = self.root / "work" / "in-progress" / "resume-me.md"
        task.write_text(task_text("Resume Me", "IN_PROGRESS", "Run the focused test next."))

        packet = build_packet(self.args())

        self.assertIn("?? dirty.txt", packet)
        self.assertIn("Initial commit", packet)
        self.assertIn("`work/in-progress/resume-me.md` | IN_PROGRESS | Resume Me", packet)
        self.assertIn("checkpoint: Run the focused test next.", packet)
        self.assertNotIn("First activity.", packet)
        self.assertIn("Latest activity.", packet)
        self.assertIn("Use this as a retrieval map", packet)

    def test_limits_recent_done_tasks(self) -> None:
        for index in range(5):
            path = self.root / "work" / "done" / f"done-{index}.md"
            path.write_text(task_text(f"Done {index}", "DONE"))

        args = self.args()
        args.max_done = 2
        packet = build_packet(args)

        self.assertEqual(packet.count("| updated unknown-date | Done"), 2)


if __name__ == "__main__":
    unittest.main()
