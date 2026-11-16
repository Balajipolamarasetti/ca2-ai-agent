from semantic_kernel.functions import kernel_function

from .common import dump_state, load_state


def rationale_for(profile: dict) -> str:
    matched = [item["name"] for item in profile.get("requirement_results", []) if item["matched"]]
    if matched:
        return f"Matched job requirements: {', '.join(matched)} ({profile.get('score', 0):g}/100)."
    return f"No listed job requirements were evidenced ({profile.get('score', 0):g}/100)."


class RankerAgent:
    """Order candidates by requirement score and write evidence-based rationales."""

    @kernel_function(name="run", description="Rank candidates and produce a concise rationale for each.")
    def run(self, payload: str) -> str:
        state = load_state(payload)
        ranked = sorted(
            state.get("candidate_pool", []),
            key=lambda profile: (-float(profile.get("score", 0)), profile["candidate_id"]),
        )
        for rank, profile in enumerate(ranked, start=1):
            profile["rank"] = rank
            profile["rationale"] = rationale_for(profile)
        state["candidate_pool"] = ranked
        return dump_state(state)
