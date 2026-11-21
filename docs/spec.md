# JobFit Agent: System Requirements and User Journey

Nov 21, 2026 · Wazed

## Overview

JobFit Agent is a Python agent that reads a job post, checks it against my profile and my job-search rules, and returns an apply or skip verdict with a match score, the gaps and the next action. I am building it to turn the job-fit process I run by hand into an agentic workflow I own end to end, and to learn how to observe and evaluate an LLM system.

**Why it exists**

- I review many backend job posts a week, and each one takes 10 to 20 minutes to judge properly.
- My rules are specific: remote roles open to Bangladesh, or relocation only with visa support stated; a 75% match cutoff; no claims I cannot back up (for example, no professional Kubernetes).
- A plain keyword filter cannot read "Python or Go" style requirements, or tell a must-have from a nice-to-have. An LLM can, if it is checked.

**Success criteria for v1**

- Agrees with my own verdict (apply or skip) on at least 12 of 15 labeled job posts.
- Every run is traced in Langfuse: inputs, each LLM and tool call, tokens, cost and latency.
- Returns a structured result in under 30 seconds and under $0.05 per job post.
- I can explain every part of the code in a 5-minute video and in interviews.

## User journey

The user is me: a backend engineer judging job posts. One run takes a job post in and gives back a verdict I can act on.

1. **Provide the job.** I paste a job post's text, or give a URL, through the CLI or `POST /evaluate`.
2. **Fetch and clean.** If it is a URL, the agent fetches the page and strips it to plain text. If the fetch fails, it asks me to paste the text.
3. **Extract requirements.** The LLM turns the post into structured data: title, company, location, work mode, visa or relocation support, years required, must-haves, nice-to-haves and salary.
4. **Apply hard rules.** Plain Python, not the LLM, checks the deal-breakers: is the role open to someone in Bangladesh, and is visa support stated for relocation roles? A failed hard rule ends the run as Skip with the reason.
5. **Score the fit.** The agent compares each requirement with my profile file and marks it met, partly met or missing, with evidence quoted from my profile. Python computes the match % from those marks.
6. **Decide.** 75% or more and no deal-breakers means Apply. The agent also lists the gaps and what to highlight in my resume.
7. **Save and show.** The result is printed, saved to a local SQLite history and optionally written to Notion. The run's trace link is printed too.
8. **Give feedback.** I mark whether I agree with the verdict. My label goes to Langfuse as a score and into the eval set if useful.

## Functional requirements

**Must have (v1)**

1. Accept a job post as raw text or a URL, from a CLI command and a FastAPI endpoint.
2. Fetch a URL with httpx and convert the HTML to clean text; fail clearly on blocked or empty pages.
3. Extract job requirements into a Pydantic model using the LLM's structured output; retry once if validation fails.
4. Load my profile (skills, years, experience facts, location, job-search rules) from a versioned `profile.yaml`.
5. Run hard-rule filters in plain Python before any scoring call.
6. Score each requirement as met, partial or missing, with a one-line evidence quote from the profile.
7. Treat "X, Y or Z" requirements as one requirement met by any option.
8. Compute the match % in code, not by asking the LLM for a number.
9. Return a result with verdict, match %, gaps, highlights and reasons, as JSON and as readable CLI output.
10. Store every run (input, output, model, prompt version, cost, trace id) in SQLite.
11. Trace every run in Langfuse and attach my agree or disagree label as a score.
12. Run an offline eval over a labeled dataset with one command and print agreement, false applies and false skips.

**Later (v2 and after)**

- Write results to my Notion job tracker.
- Draft resume bullet suggestions for Apply verdicts.
- Scheduled search: pull new posts from a few job boards daily.
- Compare two models or prompt versions on the same eval set.

## Non-functional requirements

| Area | Requirement |
| --- | --- |
| Correctness | Same input gives the same verdict at least 9 of 10 times (temperature 0, structured output) |
| Latency | Under 30 seconds per job post, end to end |
| Cost | Under $0.05 per job post; cost recorded per run |
| Reliability | LLM and fetch calls have timeouts and one retry; a failure returns a clear error, never a guessed verdict |
| Honesty | The agent never says a requirement is met without an evidence quote from the profile |
| Security | API keys only in `.env`, never committed; job page text is treated as data, never as instructions to the agent |
| Maintainability | Prompts live in versioned files; unit tests for hard rules and scoring math; type hints and ruff |
| Observability | Every LLM call, tool call and decision is visible in one Langfuse trace |

## Architecture

```
 Input (CLI / POST /evaluate)
   |  text or URL
   v
 1. Fetch (httpx + trafilatura)        -> fail: ask user to paste text
   |  plain text
   v
 2. Extract (LLM #1)                   -> JobPost (Pydantic), retry once
   |
   v
 3. Hard rules (Python)                -> fail: Skip + reason, stop
   |
   v
 4. Score (LLM #2)                     -> RequirementMatch[] with evidence
   |
   v
 5. Decide (Python)                    -> match %, verdict, gaps, highlights
   |
   v
 6. Save + show (SQLite, CLI/JSON, trace link)

 Langfuse: one trace per run, one span per step
```

The LLM only does what code cannot: reading a messy job post and matching requirements to evidence. Deal-breakers, the match % and the final verdict are plain Python, so they are testable and give the same answer every time.

## Data model

Three Pydantic models carry the data between steps; SQLite stores one row per run.

```python
class JobPost(BaseModel):
    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    location: str
    work_mode: Literal["remote", "hybrid", "onsite"]
    open_to_bd: bool | None          # None = not stated
    visa_support: bool | None
    years_required: int | None
    must_haves: list[Requirement]
    nice_to_haves: list[Requirement]
    salary: str | None


class Requirement(BaseModel):
    text: str  # as written in the post
    options: list[str]  # "Python or Go" -> ["Python", "Go"]


class RequirementMatch(BaseModel):
    requirement: str
    status: Literal["met", "partial", "missing"]
    evidence: str | None  # quote from profile.yaml; required unless missing


class Evaluation(BaseModel):
    verdict: Literal["apply", "skip"]
    match_pct: int  # computed in code
    deal_breakers: list[str]
    matches: list[RequirementMatch]
    gaps: list[str]
    highlights: list[str]  # what to put first in the resume
    prompt_version: str
    trace_id: str
```

**Scoring rule (in code):** must-haves count 2 points, nice-to-haves 1; met = full points, partial = half, missing = 0. Match % = points earned / points possible.

**`runs` table (SQLite):** id, created_at, source_url, job_text_hash, model, prompt_version, evaluation_json, cost_usd, latency_ms, trace_id, my_label (agree / disagree / null).

## Observability and evaluation

I observe the agent through Langfuse traces and judge its quality against a dataset I label myself.

**Observe (every run)**

- One Langfuse trace per run, with a span per step: fetch, extract, hard rules, score, decide.
- Each LLM call logs the prompt version, model, input, output, tokens, cost and latency.
- Hard-rule results and the final verdict are logged as span metadata, so a wrong Skip is traceable to its rule.
- My agree or disagree label is attached to the trace as a score.

**Evaluate (offline, before every prompt or model change)**

- Dataset: 15 job posts to start (Constructor, Evaboot, roles I applied to, roles I was rejected from, and clear mismatches), each labeled by me with verdict and expected must-haves. Stored as a Langfuse dataset and as `evals/jobs.jsonl`.
- Command: `python -m jobfit.eval` runs every item and reports:

| Metric | Target for v1 |
| --- | --- |
| Verdict agreement with my labels | 12 of 15 or better |
| False Apply (agent says apply, I say skip) | 1 or fewer |
| Requirement extraction recall vs my list | 80% or better |
| Evidence present for every "met" | 100% |
| Same verdict across 3 repeated runs | 14 of 15 or better |

- False Apply is the costliest error: it wastes an application and a tailored resume, so it gets its own number.

## Tech stack and project structure

Python 3.15 throughout, with one LLM provider behind a small client wrapper so the model can be swapped.

| Layer | Choice | Why |
| --- | --- | --- |
| Language | Python 3.15, uv for packages | Latest stable; all deps verified to install on it |
| API and CLI | FastAPI + Typer | FastAPI is already in my stack; Typer for quick local runs |
| LLM | Gemini free tier via `google-genai`, with structured output | $0 budget; swappable behind `llm.py` |
| Validation | Pydantic v2 | Typed outputs; a failed parse is a visible error |
| Fetching | httpx + selectolax or trafilatura | Fast HTML to text |
| Storage | SQLite (via sqlite3 or SQLModel) | Zero setup; enough for one user |
| Tracing and evals | Langfuse (cloud free tier) | Evaboot's bonus skill; traces, scores and datasets in one place |
| Quality | pytest, ruff, mypy | Tests for rules and scoring math |
| Deploy (optional) | Docker on AWS EC2 or App Runner | Evaboot's other bonus skill |

```
jobfit-agent/
  pyproject.toml
  .env.example
  profile.yaml            # my skills, facts and rules
  prompts/
    extract_v1.md
    score_v1.md
  jobfit/
    api.py                # FastAPI: POST /evaluate
    cli.py                # Typer: jobfit eval <url|file>
    agent.py              # orchestrates the steps
    fetch.py
    llm.py                # provider wrapper + tracing
    rules.py              # hard rules, plain Python
    scoring.py            # match % math
    models.py             # Pydantic models
    store.py              # SQLite
    eval.py               # offline eval runner
  evals/jobs.jsonl
  tests/
```

## Build plan

Build in thin vertical slices so something works end to end after milestone 2. Each milestone ends with a commit and a note in `LEARNING.md` (raw material for the video).

- [ ] **M1. Skeleton (1 to 2 h):** repo, uv, ruff, pytest, `.env`, `profile.yaml`, Pydantic models, and one LLM call that returns a `JobPost` from pasted text.
- [ ] **M2. End to end (2 to 3 h):** hard rules + scoring + verdict, printed from the CLI. Unit tests for `rules.py` and `scoring.py`.
- [ ] **M3. Tracing (1 h):** Langfuse on every step; check one trace in the UI and read its cost and latency.
- [ ] **M4. Eval set (2 h):** label 15 job posts by hand in `evals/jobs.jsonl`; build `jobfit.eval`; record the first agreement number, even if it is bad.
- [ ] **M5. Improve (2 to 3 h):** fix the top failure from M4 (likely "or" requirements or must-have vs nice-to-have), bump the prompt version, rerun the eval, compare numbers.
- [ ] **M6. Inputs and storage (1 to 2 h):** URL fetching, SQLite history, FastAPI endpoint, agree or disagree feedback.
- [ ] **M7. Video prep (1 h):** README with the architecture diagram; rehearse the 5-minute walkthrough twice.

**Rule for myself:** I use agentic coding to go faster, but I read, run and can explain every file before committing it.

## Mapping to the Evaboot video

Each of Evaboot's four questions maps to a part of this project I will have built and measured.

| Their question | What I show | Time |
| --- | --- | --- |
| Architecture and why | The diagram above; why hard rules are plain Python and the match % is computed in code, not by the LLM | 0:00 to 1:30 |
| How I observe and assess quality | A live Langfuse trace; the eval command and its agreement, false-Apply and consistency numbers | 1:30 to 2:45 |
| Problems and hardest parts | Real failures from M4 and how M5 changed the numbers | 2:45 to 4:00 |
| What I learned and still figuring out | What I would do next, and open questions such as how to evaluate without labeling everything by hand | 4:00 to 5:00 |

I will say plainly that this is a recent project built to learn agentic systems. The numbers in the video must be the real ones from my eval runs.
