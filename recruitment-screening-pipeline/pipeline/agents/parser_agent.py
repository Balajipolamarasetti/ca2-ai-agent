import re

from semantic_kernel.functions import kernel_function

from .common import dump_state, load_state


class ParserAgent:
    """Extract a minimal, job-relevant profile from resume text."""

    SKILLS = (
        "python",
        "sql",
        "excel",
        "tableau",
        "power bi",
        "data visualization",
        "communication",
        "stakeholder management",
        "azure",
        "machine learning",
        "project management",
        "java",
        "c#",
        "aws",
    )

    @kernel_function(name="run", description="Parse resumes into job-relevant candidate profiles.")
    def run(self, payload: str) -> str:
        state = load_state(payload)
        profiles = []
        for resume in state.get("resumes", []):
            text = str(resume.get("text", ""))
            lowered = text.casefold()
            skills = [
                skill
                for skill in self.SKILLS
                if re.search(r"(?<!\w)" + re.escape(skill) + r"(?!\w)", lowered)
            ]
            years_match = re.search(
                r"\b(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\b", lowered
            )
            education = []
            for label, pattern in (
                ("phd", r"\b(ph\.d\.?|phd|doctorate)\b"),
                ("master", r"\b(master(?:'s)?|msc|mba)\b"),
                ("bachelor", r"\b(bachelor(?:'s)?|bsc|ba|beng)\b"),
                ("associate", r"\b(associate(?:'s)? degree)\b"),
            ):
                if re.search(pattern, lowered):
                    education.append(label)

            profiles.append(
                {
                    "candidate_id": str(resume.get("candidate_id", "unknown")),
                    "skills": skills,
                    "experience_years": float(years_match.group(1)) if years_match else None,
                    "education": education,
                }
            )

        state["candidate_pool"] = profiles
        state.pop("resumes", None)
        return dump_state(state)
