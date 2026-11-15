import unittest

from pipeline.coordinator import PipelineCoordinator


JOB = {
    "title": "Data Analyst",
    "requirements": [
        {"name": "SQL querying", "kind": "skill", "expected": "sql", "weight": 2},
        {"name": "Python", "kind": "skill", "expected": "python", "weight": 1},
        {"name": "Two years experience", "kind": "experience", "expected": 2, "weight": 1},
        {"name": "Bachelor education", "kind": "education", "expected": "bachelor", "weight": 1},
    ],
}

RESUMES = [
    {
        "candidate_id": "C-01",
        "text": "Skills: SQL, Python, Tableau. 4 years experience. BSc in Statistics.",
    },
    {
        "candidate_id": "C-02",
        "text": "Skills: SQL, Excel. 1 year experience. Bachelor's degree.",
    },
    {
        "candidate_id": "C-03",
        "text": "Skills: Python, Excel. Experience dates: 2020-2024. Master's degree.",
    },
]


class PipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_sequential_scoring_review_and_scheduling(self) -> None:
        slots = [
            {"slot_id": "S1", "start": "2026-12-01T09:00:00"},
            {"slot_id": "S2", "start": "2026-12-01T10:00:00"},
        ]
        result = await PipelineCoordinator(slots).run(JOB, RESUMES, top_n=2)
        pool = result["candidate_pool"]

        self.assertEqual([item["candidate_id"] for item in pool], ["C-01", "C-02", "C-03"])
        self.assertEqual(pool[0]["score"], 100.0)
        self.assertTrue(all(item["bias_review"]["passed"] for item in pool))
        self.assertEqual(pool[0]["interview_slot"]["slot_id"], "S1")
        self.assertEqual(pool[1]["interview_slot"]["slot_id"], "S2")
        self.assertIsNone(pool[2]["interview_slot"])
        self.assertNotIn("resumes", result)
        self.assertEqual(
            [entry.get("agent") for entry in result["trace"] if "agent" in entry],
            ["parser", "matcher", "ranker", "reviewer", "scheduler"],
        )
        self.assertTrue(any(entry.get("tool") == "availability.reserve_slot" for entry in result["trace"]))

    async def test_explicit_protected_attribute_is_not_parsed_or_scored(self) -> None:
        resume = {
            "candidate_id": "C-04",
            "text": "Gender: female. Age: 28. Skills: SQL. 3 years experience. BSc.",
        }
        result = await PipelineCoordinator().run(JOB, [resume])
        profile = result["candidate_pool"][0]

        self.assertNotIn("gender", profile)
        self.assertNotIn("age", profile)
        self.assertEqual(profile["scored_fields"], ["skills", "experience_years", "education"])
        self.assertTrue(profile["bias_review"]["passed"])

    async def test_no_slots_leaves_top_candidates_unscheduled(self) -> None:
        result = await PipelineCoordinator([]).run(JOB, RESUMES, top_n=2)
        self.assertTrue(all(item["interview_slot"] is None for item in result["candidate_pool"]))

    async def test_reviewer_removes_protected_requirement_from_score(self) -> None:
        job = {
            "title": "Analyst",
            "requirements": [
                {"name": "Age preference", "kind": "skill", "expected": "sql", "weight": 100},
                {"name": "Python", "kind": "skill", "expected": "python", "weight": 1},
            ],
        }
        resumes = [
            {"candidate_id": "C-10", "text": "SQL and Python"},
            {"candidate_id": "C-11", "text": "Python"},
        ]
        result = await PipelineCoordinator([]).run(job, resumes, top_n=0)
        pool = result["candidate_pool"]

        self.assertEqual([item["candidate_id"] for item in pool], ["C-10", "C-11"])
        self.assertEqual([item["score"] for item in pool], [100.0, 100.0])
        self.assertFalse(pool[0]["bias_review"]["passed"])
        self.assertNotIn("age", pool[0]["rationale"].casefold())


if __name__ == "__main__":
    unittest.main()