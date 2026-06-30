"""Tests for task_lease.py — claim, renew, release, submit, complete, reclaim, and ID resolution."""

from __future__ import annotations

import tempfile
import unittest
from argparse import Namespace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from scripts.task_lease import (
    append_activity,
    apply_action,
    resolve_task_path,
    split_task,
    task_text,
)

NOW = datetime(2026, 5, 31, 14, 0, 0, tzinfo=timezone.utc).astimezone()
LATER = NOW + timedelta(hours=2)

READY_FRONT = {
    "id": "task-2026-05-31-example",
    "title": "Example task",
    "status": "READY",
    "agent": "unassigned",
}
READY_BODY = "\n## What\n\nExample.\n\n## Activity\n\n## Linked Nodes\n"

IN_PROGRESS_FRONT = {
    "id": "task-2026-05-31-example",
    "title": "Example task",
    "status": "IN_PROGRESS",
    "agent": "claude",
    "claimed_at": "2026-05-31T14:00:00+00:00",
    "lease_until": "2026-05-31T16:00:00+00:00",
    "session_id": "sess-abc",
}
REVIEW_PROOF = (
    "\n## Review Proof\n\n"
    "### DoD Evidence\n\n"
    "- DoD: Example.\n"
    "  Evidence: Test fixture.\n"
    "  Result: Passed.\n\n"
    "### See It Work\n\n"
    "- How Leo can inspect: Test fixture.\n"
    "- Live run status: Not applicable.\n"
    "- Residual risk: None.\n"
)
IN_PROGRESS_BODY = "\n## What\n\nExample.\n" + REVIEW_PROOF + "\n## Activity\n\n## Linked Nodes\n"
IN_PROGRESS_BODY_NO_PROOF = "\n## What\n\nExample.\n\n## Activity\n\n## Linked Nodes\n"


def make_task(directory: Path, filename: str, front: dict, body: str) -> Path:
    path = directory / filename
    path.write_text(task_text(front, body))
    return path


def base_args(tmp: Path, action: str, task: Path, session_id: str = "sess-abc") -> Namespace:
    return Namespace(
        action=action,
        task=task,
        agent="claude",
        session_id=session_id,
        minutes=120,
        work_root=tmp,
        now=NOW,
    )


class TestAppendActivity(unittest.TestCase):
    def test_uses_exact_activity_heading_when_title_contains_activity(self):
        body = (
            "\n# Backfill Activity Authors\n\n"
            "## What\n\n"
            "This paragraph mentions ## Activity but is not the section.\n\n"
            "## Activity\n\n"
            "## Linked Nodes\n"
        )

        updated = append_activity(body, NOW, "codex", "Submitted for review.")

        self.assertIn("This paragraph mentions ## Activity but is not the section.\n\n## Activity", updated)
        expected_time = NOW.strftime("%Y-%m-%d %H:%M")
        self.assertIn(f"- {expected_time} | codex | Submitted for review.\n\n## Linked Nodes", updated)


class TestClaim(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "ready").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_claim_moves_to_in_progress(self):
        path = make_task(self.root / "ready", "example.md", READY_FRONT, READY_BODY)
        args = base_args(self.root, "claim", path)
        dest = apply_action(args)
        self.assertEqual(dest.parent.name, "in-progress")
        meta, _ = split_task(dest)
        self.assertEqual(meta["status"], "IN_PROGRESS")
        self.assertEqual(meta["agent"], "claude")
        self.assertEqual(meta["session_id"], "sess-abc")

    def test_claim_fails_on_non_ready(self):
        (self.root / "in-progress").mkdir()
        front = dict(IN_PROGRESS_FRONT)
        path = make_task(self.root / "in-progress", "example.md", front, IN_PROGRESS_BODY)
        args = base_args(self.root, "claim", path)
        with self.assertRaises((ValueError, SystemExit)):
            apply_action(args)


class TestRelease(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "in-progress").mkdir()
        (self.root / "ready").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_release_returns_to_ready(self):
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        args = base_args(self.root, "release", path)
        dest = apply_action(args)
        self.assertEqual(dest.parent.name, "ready")
        meta, _ = split_task(dest)
        self.assertEqual(meta["status"], "READY")
        self.assertNotIn("session_id", meta)
        self.assertNotIn("lease_until", meta)

    def test_release_wrong_session_fails(self):
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        args = base_args(self.root, "release", path, session_id="wrong-session")
        with self.assertRaises((ValueError, SystemExit)):
            apply_action(args)

    @patch("scripts.task_lease.update_presence_best_effort")
    def test_release_stops_presence(self, update_presence):
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        apply_action(base_args(self.root, "release", path))
        update_presence.assert_called_once()
        self.assertEqual(update_presence.call_args.args, ("stop",))


class TestRenew(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "in-progress").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    @patch("scripts.task_lease.update_presence_best_effort")
    def test_renew_heartbeats_presence(self, update_presence):
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        apply_action(base_args(self.root, "renew", path))
        update_presence.assert_called_once()
        self.assertEqual(update_presence.call_args.args, ("heartbeat",))


class TestSubmit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "in-progress").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_submit_moves_to_review(self):
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        args = base_args(self.root, "submit", path)
        dest = apply_action(args)
        self.assertEqual(dest.parent.name, "review")
        meta, _ = split_task(dest)
        self.assertEqual(meta["status"], "REVIEW")
        self.assertNotIn("session_id", meta)
        self.assertNotIn("lease_until", meta)
        self.assertNotIn("claimed_at", meta)

    def test_submit_appends_activity(self):
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        args = base_args(self.root, "submit", path)
        dest = apply_action(args)
        _, body = split_task(dest)
        self.assertIn("Leo review", body)

    def test_submit_wrong_session_fails(self):
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        args = base_args(self.root, "submit", path, session_id="wrong")
        with self.assertRaises((ValueError, SystemExit)):
            apply_action(args)

    def test_submit_rejects_unchecked_definition_of_done(self):
        body = IN_PROGRESS_BODY + "\n## Definition of Done\n\n- [ ] Finish.\n"
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, body)
        with self.assertRaisesRegex(ValueError, "must be checked"):
            apply_action(base_args(self.root, "submit", path))

    def test_submit_rejects_missing_review_proof(self):
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY_NO_PROOF)
        with self.assertRaisesRegex(ValueError, "Review Proof"):
            apply_action(base_args(self.root, "submit", path))

    def test_submit_rejects_incomplete_review_proof(self):
        body = "\n## What\n\nExample.\n\n## Review Proof\n\n### DoD Evidence\n\n- Evidence only.\n\n## Activity\n\n"
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, body)
        with self.assertRaisesRegex(ValueError, "See It Work"):
            apply_action(base_args(self.root, "submit", path))

    def test_submit_by_id(self):
        make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        args = base_args(self.root, "submit", Path("task-2026-05-31-example"))
        dest = apply_action(args)
        self.assertEqual(dest.parent.name, "review")

    @patch("scripts.task_lease.update_presence_best_effort")
    def test_submit_waits_presence(self, update_presence):
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        apply_action(base_args(self.root, "submit", path))
        update_presence.assert_called_once()
        self.assertEqual(update_presence.call_args.args, ("wait",))


class TestComplete(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "in-progress").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_complete_moves_to_done(self):
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        args = base_args(self.root, "complete", path)
        dest = apply_action(args)
        self.assertEqual(dest.parent.name, "done")
        meta, _ = split_task(dest)
        self.assertEqual(meta["status"], "DONE")
        self.assertNotIn("session_id", meta)
        self.assertNotIn("lease_until", meta)
        self.assertNotIn("claimed_at", meta)

    def test_complete_sets_completed_at(self):
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        args = base_args(self.root, "complete", path)
        dest = apply_action(args)
        meta, _ = split_task(dest)
        self.assertEqual(meta.get("completed_at"), NOW.date().isoformat())

    def test_complete_appends_activity(self):
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        args = base_args(self.root, "complete", path)
        dest = apply_action(args)
        _, body = split_task(dest)
        self.assertIn("Marked task complete", body)

    def test_complete_normalizes_single_newline_at_eof(self):
        body = IN_PROGRESS_BODY + "\n\n"
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, body)
        dest = apply_action(base_args(self.root, "complete", path))
        self.assertTrue(dest.read_text().endswith("## Linked Nodes\n"))
        self.assertFalse(dest.read_text().endswith("\n\n"))

    def test_complete_blocked_by_leo_review_required(self):
        front = dict(IN_PROGRESS_FRONT, leo_review_required=True)
        path = make_task(self.root / "in-progress", "example.md", front, IN_PROGRESS_BODY)
        args = base_args(self.root, "complete", path)
        with self.assertRaises((ValueError, SystemExit)):
            apply_action(args)

    def test_complete_allowed_when_leo_review_not_required(self):
        front = dict(IN_PROGRESS_FRONT, leo_review_required=False)
        path = make_task(self.root / "in-progress", "example.md", front, IN_PROGRESS_BODY)
        args = base_args(self.root, "complete", path)
        dest = apply_action(args)
        self.assertEqual(dest.parent.name, "done")

    def test_complete_wrong_session_fails(self):
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        args = base_args(self.root, "complete", path, session_id="wrong")
        with self.assertRaises((ValueError, SystemExit)):
            apply_action(args)

    def test_complete_rejects_unchecked_definition_of_done(self):
        body = IN_PROGRESS_BODY + "\n## Definition of Done\n\n- [ ] Finish.\n"
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, body)
        with self.assertRaisesRegex(ValueError, "must be checked"):
            apply_action(base_args(self.root, "complete", path))

    def test_complete_rejects_missing_review_proof(self):
        path = make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY_NO_PROOF)
        with self.assertRaisesRegex(ValueError, "Review Proof"):
            apply_action(base_args(self.root, "complete", path))

    def test_complete_requires_in_progress(self):
        (self.root / "ready").mkdir()
        path = make_task(self.root / "ready", "example.md", READY_FRONT, READY_BODY)
        args = base_args(self.root, "complete", path)
        with self.assertRaises((ValueError, SystemExit)):
            apply_action(args)


class TestIDResolution(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "ready").mkdir()
        (self.root / "in-progress").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_file_path_returned_as_is(self):
        path = make_task(self.root / "ready", "example.md", READY_FRONT, READY_BODY)
        result = resolve_task_path(path, self.root, "claim")
        self.assertEqual(result, path.resolve())

    def test_task_id_resolves_to_ready_for_claim(self):
        make_task(self.root / "ready", "example.md", READY_FRONT, READY_BODY)
        task_id = Path("task-2026-05-31-example")
        result = resolve_task_path(task_id, self.root, "claim")
        self.assertEqual(result.name, "example.md")
        self.assertEqual(result.parent.name, "ready")

    def test_task_id_resolves_to_in_progress_for_release(self):
        make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        task_id = Path("task-2026-05-31-example")
        result = resolve_task_path(task_id, self.root, "release")
        self.assertEqual(result.parent.name, "in-progress")

    def test_task_id_resolves_to_in_progress_for_complete(self):
        make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        task_id = Path("task-2026-05-31-example")
        result = resolve_task_path(task_id, self.root, "complete")
        self.assertEqual(result.parent.name, "in-progress")

    def test_task_id_resolves_to_in_progress_for_submit(self):
        make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        task_id = Path("task-2026-05-31-example")
        result = resolve_task_path(task_id, self.root, "submit")
        self.assertEqual(result.parent.name, "in-progress")

    def test_task_id_not_found_raises(self):
        task_id = Path("task-2026-05-31-nonexistent")
        with self.assertRaises(ValueError):
            resolve_task_path(task_id, self.root, "claim")

    def test_invalid_path_raises(self):
        with self.assertRaises(ValueError):
            resolve_task_path(Path("not-a-task-id"), self.root, "claim")

    def test_claim_by_id_end_to_end(self):
        """Passing a bare task ID to claim should work the same as a full path."""
        make_task(self.root / "ready", "example.md", READY_FRONT, READY_BODY)
        task_id = Path("task-2026-05-31-example")
        args = base_args(self.root, "claim", task_id)
        dest = apply_action(args)
        self.assertEqual(dest.parent.name, "in-progress")
        meta, _ = split_task(dest)
        self.assertEqual(meta["status"], "IN_PROGRESS")

    def test_complete_by_id_end_to_end(self):
        """Passing a bare task ID to complete should work the same as a full path."""
        make_task(self.root / "in-progress", "example.md", IN_PROGRESS_FRONT, IN_PROGRESS_BODY)
        task_id = Path("task-2026-05-31-example")
        args = base_args(self.root, "complete", task_id)
        dest = apply_action(args)
        self.assertEqual(dest.parent.name, "done")
        meta, _ = split_task(dest)
        self.assertEqual(meta["status"], "DONE")


if __name__ == "__main__":
    unittest.main()
