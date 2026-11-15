import copy
import json
from typing import Any


class PipelineMemory:
    """Shared in-memory state passed from one pipeline stage to the next."""

    def __init__(self, initial_state: dict[str, Any]) -> None:
        self.state = copy.deepcopy(initial_state)
        self.trace: list[dict[str, Any]] = []

    def payload(self) -> str:
        return json.dumps(self.state, ensure_ascii=True)

    def replace(self, state: dict[str, Any]) -> None:
        self.state = state

    def record(self, event: dict[str, Any]) -> None:
        self.trace.append(event)
