# Recruitment Screening and Interview Scheduling Pipeline

This Q4 project implements a sequential multi-agent workflow using Microsoft Semantic Kernel. The Parser, Matcher, Ranker, Reviewer, and Scheduler are separate Python modules registered as Semantic Kernel plugins. The Coordinator invokes each stage in order and carries a shared in-memory candidate pool between stages. The demo uses deterministic Python functions so it runs without model credentials; the framework manages the stage/tool invocation.

The Matcher scores only named job requirements and records whether each was met plus the profile evidence used. The Bias-Guard Reviewer checks rationale text and the fields supplied to ranking for protected-attribute use, flags issues, and replaces a flagged rationale with one grounded only in requirement evidence. Resume text is discarded after parsing; the pipeline is a screening aid, not a hiring decision system.

The parser recognizes a bounded set of skill and education terms and explicit phrases such as `3 years`; it does not infer dates or unstated qualifications. An honest failure case is a resume that lists employment dates but not a duration: experience remains unknown, so the experience requirement is not credited. Run `python -m pip install -r requirements.txt`, then execute `demo.ipynb` or run `python -m unittest discover -s tests -v`.
