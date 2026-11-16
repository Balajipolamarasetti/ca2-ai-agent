# Recruitment Screening and Interview Scheduling Pipeline

A small, deterministic Python demo of a multi-stage recruitment screening workflow. It uses [Microsoft Semantic Kernel](https://github.com/microsoft/semantic-kernel) to register and invoke local Python functions as plugins; it does not call an AI model or require model credentials.

> **Prototype, not a hiring decision system.** The parser recognizes only a limited set of terms, and the bias reviewer uses simple keyword checks. Neither is sufficient to establish candidate suitability, fairness, or legal compliance. Use this project for demonstration and learning, not to make or automate real employment decisions.

## What it does

The coordinator passes a shared candidate pool through these stages:

1. **Parser** — extracts recognized skills, explicitly stated experience durations, and education terms from each resume.
2. **Matcher** — compares each profile with the job's named requirements and records evidence for each match.
3. **Ranker** — calculates a weighted score, sorts candidates, and writes a short evidence-based rationale.
4. **Reviewer** — checks ranking fields and text for a limited set of protected-attribute terms. It flags matching requirements, excludes them from scoring, and recalculates scores.
5. **Scheduler** — offers available interview slots to the highest-ranked candidates up to `top_n`.

The coordinator also records the stages and slot-reservation results in a trace. Resume text is removed from the shared state after parsing; the returned result contains extracted profile data, not the original resume text.

## Repository layout

```text
.
├── pipeline/
│   ├── agents/
│   │   ├── parser_agent.py       # Resume text extraction
│   │   ├── matcher_agent.py      # Requirement matching and scoring
│   │   ├── ranker_agent.py      # Ordering and rationale
│   │   ├── reviewer_agent.py    # Keyword-based bias checks
│   │   └── scheduler_agent.py   # Slot assignment
│   ├── availability_tool.py     # In-memory slot listing and reservation
│   ├── coordinator.py           # Semantic Kernel setup and workflow
│   └── memory.py                # Shared state and trace
├── tests/
│   └── test_pipeline.py         # End-to-end workflow tests
├── demo.ipynb                  # Three illustrative runs
├── requirements.txt
└── README.md
```

## Requirements and setup

- Python 3.10 or later
- `semantic-kernel` 1.x (declared in `requirements.txt`)
- Jupyter to run the notebook (not installed by `requirements.txt`); alternatively, use the Python example below

Create and activate a virtual environment, then install the project dependency:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, use:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the demo

Open `demo.ipynb` in VS Code with the Jupyter extension or in Jupyter Notebook, and run its cells. It demonstrates a full shortlist, limited interview availability, and missing experience evidence alongside protected-attribute text.

The pipeline can also be called directly from Python:

```python
import asyncio

from pipeline.coordinator import PipelineCoordinator

job = {
    "title": "Data Analyst",
    "requirements": [
        {"name": "SQL querying", "kind": "skill", "expected": "sql", "weight": 2},
        {"name": "Python", "kind": "skill", "expected": "python", "weight": 1},
        {"name": "Two years experience", "kind": "experience", "expected": 2, "weight": 1},
        {"name": "Bachelor education", "kind": "education", "expected": "bachelor", "weight": 1},
    ],
}

resumes = [
    {"candidate_id": "C-01", "text": "Skills: SQL, Python. 4 years experience. BSc."},
]
slots = [{"slot_id": "S1", "start": "2026-12-01T09:00:00"}]

result = asyncio.run(PipelineCoordinator(slots).run(job, resumes, top_n=1))
for candidate in result["candidate_pool"]:
    print(candidate["candidate_id"], candidate["score"], candidate["interview_slot"])
```

In a notebook cell that supports top-level `await`, call `await PipelineCoordinator(slots).run(job, resumes, top_n=1)` instead of `asyncio.run(...)`.

## Input and scoring

`PipelineCoordinator.run(job, resumes, top_n=3)` accepts:

- A `job` dictionary with a `title` and a `requirements` list.
- A list of resumes, each with a `candidate_id` and resume `text`.
- An optional `top_n` specifying how many highest-ranked candidates may be scheduled. A negative value is treated as zero.
- Optional availability slots passed to `PipelineCoordinator`, each with a unique `slot_id` and a `start` value.

Each requirement uses:

| Field | Meaning |
| --- | --- |
| `name` | Human-readable requirement label |
| `kind` | `skill`, `experience`, or `education` |
| `expected` | Skill/education label or numeric years for experience; skill and education expectations may also be lists |
| `weight` | Non-negative contribution to the score; defaults to `1` |

The score is the percentage of eligible requirement weight matched. Requirements flagged by the reviewer are excluded from both the earned weight and the eligible total. Candidates are sorted by descending score, with `candidate_id` as the tie-breaker.

The parser recognizes a bounded skill vocabulary: Python, SQL, Excel, Tableau, Power BI, data visualization, communication, stakeholder management, Azure, machine learning, project management, Java, C#, and AWS. It recognizes explicit numeric durations such as `3 years` or `2 yrs`; it does not infer a duration from employment dates. Education extraction is limited to PhD/doctorate, master's, bachelor's, and associate degree terms.

## Result

The returned dictionary contains:

- `job` — the supplied job description.
- `candidate_pool` — all parsed candidates, ranked, with extracted fields, per-requirement match evidence, score, rationale, bias-review result, and either an assigned interview slot or `None`.
- `top_n` — the effective shortlist limit.
- `trace` — ordered agent and availability-tool events.

The original `resumes` and temporary `available_slots` are not included in the returned state. Availability is in-memory only: reservations are not persisted across runs or shared across processes.

## Run tests

From the repository root:

```powershell
python -m unittest discover -s tests -v
```

The tests cover sequential scoring, review and scheduling; omission of protected attributes from parsed profiles; behavior when there are no slots; and removal of a requirement whose name references a protected attribute.

## Known limitations

- Extraction is keyword- and regular-expression-based. Unrecognized wording, equivalent skills, date ranges, and unstated qualifications are not inferred.
- The protected-term list is not exhaustive and can miss proxies or context; a flagged phrase is not proof of unfairness, and a passing review is not proof of fairness.
- The score is a simple weighted match percentage. It is not a validated measure of candidate quality and should not be used as an automated hiring decision.
- Slots are reserved sequentially in memory, without persistence, external calendar integration, or concurrency coordination.
