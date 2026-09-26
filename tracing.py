"""Persist LiveKit's native events and the simulated store's final state."""
import json
import time
from datetime import datetime, timezone
from uuid import uuid4

from config import ROOT


class RunTrace:
    def __init__(self, task_id: str):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.directory = ROOT / "results" / f"{stamp}-task-{task_id}-{uuid4().hex[:8]}"
        self.directory.mkdir(parents=True)
        self._file = (self.directory / "events.jsonl").open("w")

    def save(self, name: str, value):
        (self.directory / name).write_text(json.dumps(value, indent=2, ensure_ascii=False))

    def emit(self, kind: str, payload: dict):
        if not self._file.closed:
            self._file.write(json.dumps({"time": time.time(), "type": kind, "data": payload}) + "\n")
            self._file.flush()

    def attach(self, session):
        for name in (
            "user_input_transcribed", "conversation_item_added", "function_tools_executed",
            "agent_state_changed", "user_state_changed", "session_usage_updated",
            "user_transcription_timeout", "error", "close",
        ):
            def handler(event, event_name=name):
                # Error.source is a runtime object, not serializable evidence.
                payload = event.model_dump(mode="json", exclude={"source"})
                if event_name == "error":
                    error = event.error.error
                    payload["error"]["exception_type"] = type(error).__name__
                    payload["error"]["status_code"] = getattr(error, "status_code", None)
                self.emit(event_name, payload)
            session.on(name, handler)

    def finish(self, session, benchmark):
        self.save("conversation.json", session.history.to_dict(exclude_timestamp=False))
        self.save("final_state.json", benchmark.snapshot())
        self.emit("run_finished", {"db_hash": benchmark.environment.get_db_hash()})
        self._file.close()
