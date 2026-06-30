from __future__ import annotations

import json
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

from scripts.agent_presence import prune_state, show_status, update_presence


class AgentPresenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state = self.root / "runs" / "agent-presence.json"
        self.events = self.root / "runs" / "agent-presence.jsonl"
        self.lock = self.root / "runs" / ".agent-presence.lock"
        self.now = datetime(2026, 5, 31, 12, 0, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def args(self, action: str, status: str, now: datetime | None = None) -> Namespace:
        return Namespace(
            action=action,
            status=status,
            state=self.state,
            events=self.events,
            lock=self.lock,
            now=now or self.now,
            agent="codex",
            provider="openai",
            session_id="thread-1",
            session_url="",
            task_id="task-example",
            role="coder",
            model="gpt-test",
            strengths=["code", "tests"],
            tools=["shell", "git"],
            cost_tier="high",
            context_tier="large",
            current_slice="Build helper",
            last_commit="",
            handoff_checkpoint="",
            minutes=45,
        )

    def test_start_and_checkpoint_update_state_and_append_events(self) -> None:
        update_presence(self.args("start", "STARTED"))
        checkpoint = self.args("checkpoint", "CHECKPOINTED", self.now + timedelta(minutes=5))
        checkpoint.last_commit = "abc123"
        checkpoint.handoff_checkpoint = "Run final test."
        update_presence(checkpoint)

        state = json.loads(self.state.read_text())["thread-1"]
        events = self.events.read_text().splitlines()
        self.assertEqual(state["status"], "CHECKPOINTED")
        self.assertEqual(state["last_commit"], "abc123")
        self.assertEqual(state["role"], "coder")
        self.assertEqual(state["strengths"], ["code", "tests"])
        self.assertEqual(len(events), 2)

    def test_status_marks_abandoned_active_session_expired(self) -> None:
        update_presence(self.args("start", "STARTED"))
        output = StringIO()
        with redirect_stdout(output):
            show_status(Namespace(state=self.state, now=self.now + timedelta(hours=1)))
        self.assertIn("EXPIRED", output.getvalue())

    def test_non_start_update_requires_registered_session(self) -> None:
        with self.assertRaisesRegex(ValueError, "run start first"):
            update_presence(self.args("heartbeat", "ACTIVE"))

    def test_status_summary_line_counts_sessions(self) -> None:
        update_presence(self.args("start", "STARTED"))
        second = self.args("start", "STARTED")
        second.session_id = "thread-2"
        update_presence(second)
        update_presence(self.args("end", "COMPLETED", self.now + timedelta(minutes=1)))
        output = StringIO()
        with redirect_stdout(output):
            show_status(Namespace(state=self.state, now=self.now + timedelta(minutes=2)))
        first_line = output.getvalue().splitlines()[0]
        self.assertIn("2 session(s):", first_line)
        self.assertIn("1 active", first_line)
        self.assertIn("1 completed", first_line)

    def test_status_formats_entry_fields_on_separate_lines(self) -> None:
        args = self.args("start", "STARTED")
        args.last_commit = "abc123"
        args.handoff_checkpoint = "Run final test."
        update_presence(args)
        output = StringIO()
        with redirect_stdout(output):
            show_status(Namespace(state=self.state, now=self.now))
        text = output.getvalue()
        self.assertIn("task:   task-example", text)
        self.assertIn("model:  gpt-test (coder)", text)
        self.assertIn("started:", text)
        self.assertIn("seen:   ", text)
        self.assertIn("commit: abc123", text)
        self.assertIn("slice:  Build helper", text)
        self.assertIn("next:   Run final test.", text)

    def test_status_json_flag_returns_array_with_visible_status(self) -> None:
        update_presence(self.args("start", "STARTED"))
        output = StringIO()
        with redirect_stdout(output):
            show_status(Namespace(state=self.state, now=self.now + timedelta(hours=1), json=True))
        data = json.loads(output.getvalue())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["visible_status"], "EXPIRED")
        self.assertIn("agent", data[0])

    def test_prune_removes_old_terminal_session(self) -> None:
        update_presence(self.args("start", "STARTED"))
        update_presence(self.args("stop", "STOPPED"))
        prune_state(
            Namespace(
                state=self.state,
                lock=self.lock,
                now=self.now + timedelta(hours=25),
                terminal_hours=24,
                expired_hours=72,
            )
        )
        self.assertEqual(json.loads(self.state.read_text()), {})

    def test_tasks_accumulate_without_duplicates(self) -> None:
        update_presence(self.args("start", "STARTED"))
        heartbeat = self.args("heartbeat", "ACTIVE", self.now + timedelta(minutes=1))
        heartbeat.task_id = "task-second"
        update_presence(heartbeat)
        checkpoint = self.args("checkpoint", "CHECKPOINTED", self.now + timedelta(minutes=2))
        checkpoint.task_id = "task-example"
        update_presence(checkpoint)

        state = json.loads(self.state.read_text())["thread-1"]
        self.assertEqual(state["task_id"], "task-example")
        self.assertEqual(state["tasks"], ["task-example", "task-second"])

    def test_end_prints_closing_summary(self) -> None:
        update_presence(self.args("start", "STARTED"))
        end = self.args("end", "COMPLETED", self.now + timedelta(minutes=45))
        end.last_commit = "fec537f"
        end.handoff_checkpoint = "Brief handoff note here."
        output = StringIO()
        with redirect_stdout(output):
            update_presence(end)

        text = output.getvalue()
        self.assertIn("Session ended: codex@openai:thread-1", text)
        self.assertIn("(45 min)", text)
        self.assertIn("tasks:   task-example", text)
        self.assertIn("commit:  fec537f", text)
        self.assertIn("next:    Brief handoff note here.", text)

    def test_complete_warns_and_records_end_event(self) -> None:
        update_presence(self.args("start", "STARTED"))
        warning = StringIO()
        with redirect_stderr(warning):
            update_presence(self.args("complete", "COMPLETED", self.now + timedelta(minutes=1)))

        events = [json.loads(line) for line in self.events.read_text().splitlines()]
        self.assertIn("complete is deprecated; use end", warning.getvalue())
        self.assertEqual(events[-1]["event"], "end")

    def test_start_after_terminal_status_begins_fresh_epoch(self) -> None:
        update_presence(self.args("start", "STARTED"))
        update_presence(self.args("end", "COMPLETED", self.now + timedelta(hours=8)))
        restart = self.args("start", "STARTED", self.now + timedelta(hours=9))
        restart.task_id = "task-follow-up"
        update_presence(restart)
        end = self.args("end", "COMPLETED", self.now + timedelta(hours=9, minutes=5))
        end.task_id = "task-follow-up"
        output = StringIO()
        with redirect_stdout(output):
            update_presence(end)

        state = json.loads(self.state.read_text())["thread-1"]
        events = [json.loads(line) for line in self.events.read_text().splitlines()]
        self.assertEqual(state["started_at"], (self.now + timedelta(hours=9)).isoformat())
        self.assertEqual(state["tasks"], ["task-follow-up"])
        self.assertEqual(events[-2]["event"], "restart")
        self.assertIn("(5 min)", output.getvalue())


if __name__ == "__main__":
    unittest.main()
