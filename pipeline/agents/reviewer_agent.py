import re

from semantic_kernel.functions import kernel_function

from .common import dump_state, load_state
from .ranker_agent import rationale_for


class ReviewerAgent:
    """Flag protected-attribute signals and ensure ranking uses job-related fields only."""

    PROTECTED_TERMS = (
        "gender",
        "race",
        "ethnicity",
        "religion",
        "disability",
        "age",
        "marital status",
        "sexual orientation",
        "national origin",
        "pregnant",
        "male",
        "female",
        "young",
        "old",
    )
    ALLOWED_SCORED_FIELDS = {"skills", "experience_years", "education"}

    @classmethod
    def _protected_terms_in(cls, value: str) -> list[str]:
        return [
            term
            for term in cls.PROTECTED_TERMS
            if re.search(r"\b" + re.escape(term) + r"\b", value.casefold())
        ]

    @kernel_function(name="run", description="Review ranking fields and rationales for protected-attribute use.")
    def run(self, payload: str) -> str:
        state = load_state(payload)
        for profile in state.get("candidate_pool", []):
            rationale = str(profile.get("rationale", ""))
            flags = [f"Rationale contains protected-attribute term: {term}." for term in self._protected_terms_in(rationale)]
            scored_fields = set(profile.get("scored_fields", []))
            unexpected_fields = sorted(scored_fields - self.ALLOWED_SCORED_FIELDS)
            if unexpected_fields:
                flags.append(f"Ranking used non-job-related fields: {', '.join(unexpected_fields)}.")
                profile["scored_fields"] = sorted(scored_fields & self.ALLOWED_SCORED_FIELDS)

            total_weight = 0.0
            achieved_weight = 0.0
            for requirement in profile.get("requirement_results", []):
                requirement_text = f"{requirement.get('name', '')} {requirement.get('expected', '')}"
                protected_terms = self._protected_terms_in(requirement_text)
                weight = max(float(requirement.get("weight", 1)), 0.0)
                if protected_terms:
                    flags.extend(
                        f"Scoring requirement references protected attribute: {term}."
                        for term in protected_terms
                    )
                    requirement["matched"] = False
                    requirement["evidence"] = "Excluded by bias review because the requirement references a protected attribute."
                else:
                    total_weight += weight
                    if requirement.get("matched"):
                        achieved_weight += weight
            profile["score"] = round(100 * achieved_weight / total_weight, 1) if total_weight else 0.0
            if flags:
                profile["rationale"] = rationale_for(profile)
            profile["bias_review"] = {"passed": not flags, "flags": flags}

        state["candidate_pool"] = sorted(
            state.get("candidate_pool", []),
            key=lambda profile: (-float(profile.get("score", 0)), profile["candidate_id"]),
        )
        for rank, profile in enumerate(state["candidate_pool"], start=1):
            profile["rank"] = rank
        return dump_state(state)
