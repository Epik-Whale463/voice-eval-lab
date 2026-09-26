"""Adapt official tau-bench tools to LiveKit; do not duplicate store logic."""
from typing import Callable

from livekit.agents import RunContext, function_tool
from livekit.agents.llm import ToolError

import config  # Configure tau-bench data location before importing it.
from tau2.data_model.message import ToolCall
from tau2.domains.retail.environment import get_environment, get_tasks


class RetailBenchmark:
    def __init__(self, task_id: str, emit: Callable):
        self.task = next((t for t in get_tasks() if t.id == task_id), None)
        if self.task is None:
            raise ValueError(f"Unknown retail task ID: {task_id}")
        self.environment = get_environment()
        initial = self.task.initial_state
        # Avoid silently dropping task history. Initial support is fresh conversations.
        if initial and initial.message_history:
            raise ValueError("This interactive runner requires a task without initial chat history")
        self.environment.set_state(
            initialization_data=initial.initialization_data if initial else None,
            initialization_actions=initial.initialization_actions if initial else None,
            message_history=[],
        )
        self.emit = emit

    @property
    def policy(self) -> str:
        return self.environment.get_policy()

    def snapshot(self) -> dict:
        return self.environment.tools.db.model_dump(mode="json")

    def execute(self, name: str, arguments: dict, call_id: str):
        self.emit("tool_started", {"call_id": call_id, "name": name, "arguments": arguments})
        response = self.environment.get_response(
            ToolCall(id=call_id, name=name, arguments=arguments)
        )
        self.emit("tool_finished", {
            "call_id": call_id, "name": name,
            "content": response.content, "error": response.error,
            "db_hash": self.environment.get_db_hash(),
        })
        return response

    def tools(self) -> list:
        def wrap(tool):
            async def execute(raw_arguments: dict, context: RunContext):
                response = self.execute(tool.name, raw_arguments, context.function_call.call_id)
                if response.error:
                    raise ToolError(response.content)
                return response.content

            return function_tool(execute, raw_schema=tool.openai_schema["function"])

        return [wrap(tool) for tool in self.environment.get_tools()]
