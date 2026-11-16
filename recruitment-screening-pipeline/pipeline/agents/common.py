import json
from typing import Any


def load_state(payload: str) -> dict[str, Any]:
    state = json.loads(payload)
    if not isinstance(state, dict):
        raise ValueError("Agent input must be a JSON object.")
    return state


def dump_state(state: dict[str, Any]) -> str:
    return json.dumps(state, ensure_ascii=True)
