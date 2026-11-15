import json

from semantic_kernel.functions import kernel_function


class AvailabilityTool:
    """In-memory interview availability source with slot reservation."""

    def __init__(self, slots: list[dict[str, str]]) -> None:
        self._slots = [dict(slot) for slot in slots]
        self._reserved: set[str] = set()

    @kernel_function(name="list_available_slots", description="Return currently unreserved interview slots.")
    def list_available_slots(self) -> str:
        available = [slot for slot in self._slots if slot["slot_id"] not in self._reserved]
        return json.dumps(available)

    @kernel_function(name="reserve_slot", description="Reserve an interview slot by its identifier.")
    def reserve_slot(self, slot_id: str) -> str:
        exists = any(slot["slot_id"] == slot_id for slot in self._slots)
        reserved = exists and slot_id not in self._reserved
        if reserved:
            self._reserved.add(slot_id)
        return json.dumps({"slot_id": slot_id, "reserved": reserved})
