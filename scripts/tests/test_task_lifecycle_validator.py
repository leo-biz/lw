from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.task_lifecycle_validator import validate


BODY = "\n## Definition of Done\n\n- [x] Done.\n\n## Activity\n"


def task(root: Path, folder: str, task_id: str, **metadata) -> Path:
    path = root / folder / f"{task_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    front = {"id": task_id, "status": metadata.pop("status", folder.upper().replace("-", "_")), **metadata}
    path.write_text(f"---\n{yaml.safe_dump(front, sort_keys=False).rstrip()}\n---\n{BODY}")
    return path


class TaskLifecycleValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.work = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def codes(self) -> list[str]:
        return [item["code"] for item in validate(self.work)]

    def test_detects_folder_status_and_active_lease_invariants(self) -> None:
        task(self.work, "ready", "task-2026-06-01-example", status="DONE", session_id="stale")
        self.assertIn("FOLDER_STATUS_MISMATCH", self.codes())
        self.assertIn("NON_ACTIVE_LEASE_METADATA", self.codes())

    def test_detects_in_progress_missing_ownership(self) -> None:
        task(self.work, "in-progress", "task-2026-06-01-example", agent="unassigned")
        self.assertIn("IN_PROGRESS_LEASE_MISSING", self.codes())

    def test_detects_done_checklist_and_completion_timestamp(self) -> None:
        path = task(self.work, "done", "task-2026-06-01-example")
        path.write_text(path.read_text().replace("- [x] Done.", "- [ ] Done."))
        self.assertIn("DONE_UNCHECKED_DOD", self.codes())
        self.assertIn("DONE_MISSING_COMPLETED_AT", self.codes())

    def test_detects_review_unchecked_checklist(self) -> None:
        path = task(self.work, "review", "task-2026-06-01-example")
        path.write_text(path.read_text().replace("- [x] Done.", "- [ ] Done."))
        self.assertIn("REVIEW_UNCHECKED_DOD", self.codes())

    def test_detects_stale_completed_blocker_and_reciprocal_drift(self) -> None:
        task(self.work, "done", "task-2026-06-01-dep", completed_at="2026-06-01")
        task(self.work, "ready", "task-2026-06-01-child", blocked_by="task-2026-06-01-dep", depends_on=["task-2026-06-01-dep"])
        codes = self.codes()
        self.assertIn("STALE_COMPLETED_BLOCKER", codes)
        self.assertIn("MISSING_RECIPROCAL_BLOCKING", codes)
        self.assertIn("MISSING_RECIPROCAL_DEPENDENT", codes)

    def test_detects_duplicate_task_ids(self) -> None:
        task(self.work, "ready", "task-2026-06-01-example")
        task(self.work, "someday", "task-2026-06-01-example")
        self.assertEqual(self.codes().count("DUPLICATE_TASK_ID"), 2)

    def test_detects_nondirectional_link_for_durable_dependency(self) -> None:
        path = task(self.work, "ready", "task-2026-06-01-child", depends_on=["task-2026-06-01-dep"])
        path.write_text(path.read_text() + "\n## Linked Nodes\n\n- related_to: [[../done/dep]]\n")
        task(self.work, "done", "task-2026-06-01-dep", completed_at="2026-06-01", dependents=["task-2026-06-01-child"])
        self.assertIn("NONDIRECTIONAL_DEPENDENCY_LINK", self.codes())


if __name__ == "__main__":
    unittest.main()
