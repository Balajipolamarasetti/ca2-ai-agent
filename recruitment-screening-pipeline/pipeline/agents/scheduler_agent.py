from semantic_kernel.functions import kernel_function

from .common import dump_state, load_state


class SchedulerAgent:
    """Assign available interview slots to the highest-ranked candidates."""

    @kernel_function(name="run", description="Schedule the top-ranked candidates using available slots.")
    def run(self, payload: str) -> str:
        state = load_state(payload)
        candidates = state.get("candidate_pool", [])
        slots = iter(state.get("available_slots", []))
        top_n = int(state.get("top_n", 3))

        for profile in candidates:
            profile["interview_slot"] = None
            if profile.get("rank", top_n + 1) <= top_n:
                profile["interview_slot"] = next(slots, None)
        return dump_state(state)
