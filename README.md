# JobFit Agent

A Python agent that reads a backend job post, checks it against my profile and job-search rules, and returns an **Apply** or **Skip** verdict with a match %, the gaps and what to highlight in my resume.

> Status: in progress. This is a learning project I'm building in public to get hands-on with building, tracing and evaluating an LLM agent. Every metric shown here comes from a real eval run; until a milestone is done, there are no numbers.

## Why

I review a lot of job posts, and each one takes 10 to 20 minutes to judge properly. My rules are specific (remote roles open to Bangladesh, relocation only with visa support, a 75% match cutoff, no claims I can't back up). A keyword filter can't read "Python or Go" or tell a must-have from a nice-to-have. An LLM can, if it's checked.

## How it works

```
 Input (CLI / POST /evaluate)
   |  text or URL
   v
 1. Fetch (httpx + trafilatura)        -> fail: ask user to paste text
   v
 2. Extract (LLM #1)                   -> JobPost (Pydantic), retry once
   v
 3. Hard rules (Python)                -> fail: Skip + reason, stop
   v
 4. Score (LLM #2)                     -> each requirement: met / partial / missing + evidence
   v
 5. Decide (Python)                    -> match %, verdict, gaps, highlights
   v
 6. Save + show (SQLite, CLI/JSON, Langfuse trace link)
```

**Design principle:** the LLM only does what code can't (reading a messy post, matching requirements to evidence). Deal-breakers, the match % and the verdict are plain Python, so they're testable and deterministic.

**Scoring:** must-haves are 2 points, nice-to-haves 1. Met is full points, partial is half, missing is 0. Apply if the match is 75% or more and there are no deal-breakers.

## Observability and evaluation

- **Tracing:** every run is one Langfuse trace with a span per step, including prompt version, tokens, cost and latency.
- **Offline eval:** `python -m jobfit.eval` runs a set of job posts I labeled by hand and reports:

| Metric | v1 target | Current |
| --- | --- | --- |
| Verdict agreement with my labels | 12/15+ | not run yet |
| False Apply | 1 or fewer | not run yet |
| Requirement extraction recall | 80%+ | not run yet |
| Evidence present for every "met" | 100% | not run yet |
| Same verdict across 3 repeated runs | 14/15+ | not run yet |

## Stack

Python 3.12, uv, Pydantic v2, Gemini API (via `google-genai`, behind a swappable wrapper), Typer, FastAPI, httpx, trafilatura, SQLite, Langfuse, pytest, ruff, mypy.

## Roadmap

- [ ] M1 Skeleton: project setup, models, one LLM call returning a `JobPost`
- [ ] M2 End to end: hard rules, scoring, verdict from the CLI, unit tests
- [ ] M3 Tracing with Langfuse
- [ ] M4 Labeled eval set and eval runner, first numbers
- [ ] M5 Fix the top failure, bump the prompt version, compare
- [ ] M6 URL fetch, SQLite history, FastAPI endpoint, feedback labels
- [ ] M7 Write-up and demo

## Learning in public

I build this with a learn, build, break, fix loop: get it working, break it on purpose (bad JSON, rate limits, prompt injection, rounding edges, missing spans), then find and fix the cause with a regression test. Every failure is logged in [`LEARNING.md`](LEARNING.md).

More detail: [`docs/spec.md`](docs/spec.md).

## Setup

Setup instructions will be added in M1.

## Author

Abdul Wajed Khan · [LinkedIn](https://linkedin.com/in/wajed-khan) · [GitHub](https://github.com/WazedKhan)
