from typing import Any

from semantic_kernel.functions import kernel_function

from .common import dump_state, load_state


def _match_requirement(profile: dict[str, Any], requirement: dict[str, Any]) -> tuple[bool, str]:
    kind = str(requirement.get("kind", "skill")).casefold()
    expected = requirement.get("expected", "")
    name = str(requirement.get("name", expected))

    if kind == "skill":
        expected_values = expected if isinstance(expected, list) else [expected]
        skills = {str(skill).casefold() for skill in profile.get("skills", [])}
        matched_value = next(
            (str(value) for value in expected_values if str(value).casefold() in skills),
            None,
        )
        if matched_value:
            return True, f"Profile lists the required skill {matched_value}."
        return False, f"No profile evidence for required skill {name}."

    if kind == "experience":
        years = profile.get("experience_years")
        required_years = float(expected)
        if years is not None and years >= required_years:
            return True, f"Profile states {years:g} years; requirement is {required_years:g}."
        if years is None:
            return False, "Resume does not state an explicit duration in years."
        return False, f"Profile states {years:g} years; requirement is {required_years:g}."

    if kind == "education":
        expected_values = expected if isinstance(expected, list) else [expected]
        education = {str(level).casefold() for level in profile.get("education", [])}
        matched_value = next(
            (str(value) for value in expected_values if str(value).casefold() in education),
            None,
        )
        if matched_value:
            return True, f"Profile lists {matched_value} education."
        return False, f"No profile evidence for required education: {name}."

    return False, f"Unsupported requirement type: {kind}."


class MatcherAgent:
    """Score profiles against named, weighted job requirements."""

    @kernel_function(name="run", description="Score each profile and justify every requirement result.")
    def run(self, payload: str) -> str:
        state = load_state(payload)
        requirements = state.get("job", {}).get("requirements", [])
        total_weight = sum(max(float(item.get("weight", 1)), 0.0) for item in requirements)

        for profile in state.get("candidate_pool", []):
            results = []
            achieved_weight = 0.0
            for requirement in requirements:
                matched, evidence = _match_requirement(profile, requirement)
                weight = max(float(requirement.get("weight", 1)), 0.0)
                if matched:
                    achieved_weight += weight
                results.append(
                    {
                        "name": str(requirement.get("name", requirement.get("expected", "Requirement"))),
                        "kind": str(requirement.get("kind", "skill")),
                        "expected": requirement.get("expected", ""),
                        "weight": weight,
                        "matched": matched,
                        "evidence": evidence,
                    }
                )
            profile["requirement_results"] = results
            profile["score"] = round(100 * achieved_weight / total_weight, 1) if total_weight else 0.0
            profile["scored_fields"] = ["skills", "experience_years", "education"]

        return dump_state(state)
