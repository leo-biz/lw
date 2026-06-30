from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts.agent_presence_bridge import update_presence_best_effort


class AgentPresenceBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.state = Path(self.temp.name) / "agent-presence.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    @patch("scripts.agent_presence_bridge.subprocess.run")
    def test_missing_state_is_silent_no_op(self, run) -> None:
        update_presence_best_effort("heartbeat", session_id="missing")
        run.assert_not_called()

    @patch("scripts.agent_presence_bridge.subprocess.run")
    def test_unregistered_session_is_silent_no_op(self, run) -> None:
        self.state.write_text("{}\n")
        with patch("scripts.agent_presence_bridge.PRESENCE_STATE", self.state):
            update_presence_best_effort("heartbeat", session_id="missing")
        run.assert_not_called()

    @patch("scripts.agent_presence_bridge.subprocess.run")
    def test_registered_session_invokes_presence_cli_silently(self, run) -> None:
        self.state.write_text(json.dumps({"thread-1": {"status": "STARTED"}}))
        run.return_value.returncode = 0
        with patch("scripts.agent_presence_bridge.PRESENCE_STATE", self.state):
            update_presence_best_effort(
                "checkpoint",
                session_id="thread-1",
                agent="codex",
                task_id="task-example",
                last_commit="abc123",
                current_slice="Checkpointed",
            )
        command = run.call_args.args[0]
        self.assertIn("checkpoint", command)
        self.assertIn("thread-1", command)
        self.assertIn("abc123", command)

    @patch("scripts.agent_presence_bridge.subprocess.run")
    def test_cli_failure_warns_without_raising(self, run) -> None:
        self.state.write_text(json.dumps({"thread-1": {"status": "STARTED"}}))
        run.return_value.returncode = 1
        run.return_value.stderr = "broken"
        run.return_value.stdout = ""
        error = StringIO()
        with patch("scripts.agent_presence_bridge.PRESENCE_STATE", self.state):
            with redirect_stderr(error):
                update_presence_best_effort("heartbeat", session_id="thread-1")
        self.assertIn("WARNING: presence update failed: broken", error.getvalue())


if __name__ == "__main__":
    unittest.main()
