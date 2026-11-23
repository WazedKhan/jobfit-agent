# JobFit Agent

A Python agent that reads a job post, checks it against my profile and job-search rules, and returns an Apply or Skip verdict with a match %, gaps and resume highlights.

Context files in this repo:

- `docs/spec.md`: full spec (requirements, user journey, architecture, data model, eval plan, build plan)
- `LEARNING.md`: my failure log and lesson notes, one entry per thing that broke
- `PROGRESS.md`: where the project stands, open questions and what to do next. Read this first in a new chat.
- Online spec: https://claude.ai/artifact/XKkbC7e1xAgcBjmffd6Dbz

## Why this project exists

- Portfolio project to get hands-on experience building, observing and evaluating an agentic system in Python.
- Built for a 5-minute video for Evaboot (an agentic-workflows engineer role). The video must cover: architecture and why, how I observe the agent and judge quality, problems faced, what I learned and what I'm still figuring out.
- Budget is $0: Gemini API free tier, Langfuse free plan, SQLite, run locally.

## How to work with me (instructions for Claude)

- I am the developer. I must be able to explain every line in an interview, so:
  - Work one milestone at a time. Do not jump ahead.
  - Explain the design choice before or alongside the code, briefly.
  - Keep code small and readable. No clever abstractions I did not ask for.
  - After each milestone, give me a short "what I learned" note for the video.
- Never invent numbers for the video or README. Metrics come only from real eval runs.
- I am a backend engineer (3.5 years; Python/Django/FastAPI, Go, PostgreSQL). Skip beginner explanations of Python or HTTP; do explain LLM, tracing and eval concepts.
- No em dashes in any text written for me.
- Don't guess. Read the actual code (and `git status` / `git diff`) before suggesting anything.
- Decisions come from me. Give options and trade-offs; never treat your suggestion as decided.
- Before using any library, fetch its latest official docs for the installed version. Don't rely on remembered APIs.
- Before giving commit commands, run `git status` and `git diff` on the real repo. I write code too, so don't assume you know every change. List only files that belong in the commit.
- Read `PROGRESS.md` first and follow its "Rules for Claude".
- Never run `git commit`, `git push` or any other command that changes git history. Only give me the commit message and the `git add` / `git commit` commands to run myself.

## Learning mode: learn, build, break, fix, log

The goal is that I learn this well enough to do it professionally, not just to have working code. Every milestone follows this loop:

1. **Learn**: explain the one or two LLM, tracing or eval concepts the milestone needs, then ask me 2 or 3 check questions. I answer before I write code.
2. **Build**: give me a small spec (files, function signatures, tests that must pass). I write the agent logic myself. Claude may scaffold boring setup files (pyproject, ruff config, .gitignore). Review my diff like a senior reviewer; do not rewrite it for me.
3. **Break**: once it works, give me specific failures to trigger on purpose (bad JSON, rate limits, prompt injection, rounding edges, missing spans, blocked fetches, and so on).
4. **Fix**: I diagnose from the error, trace or test. If I ask for help, give hints in levels: nudge, then where to look, then the answer.
5. **Log**: I add an entry to `LEARNING.md` (what broke, how I found it, fix, regression test, interview line).

Rules for every fix:

- Reproduce before fixing.
- Every bug gets a regression test.
- Every prompt change bumps the prompt version and reruns the eval.

## Architecture (6 steps, 2 LLM calls)

1. **Input**: CLI (Typer) or `POST /evaluate` (FastAPI); pasted text or a URL.
2. **Fetch**: httpx + HTML to text; if blocked, ask the user to paste the text.
3. **Extract (LLM)**: structured output into a `JobPost` Pydantic model; retry once on validation failure.
4. **Hard rules (Python)**: deal-breakers, e.g. remote role not open to Bangladesh, or relocation without visa support. Fail = Skip with reason.
5. **Score (LLM)**: each requirement marked met / partial / missing, with an evidence quote from `profile.yaml`. "X, Y or Z" counts as one requirement met by any option.
6. **Decide (Python)**: match % computed in code (must-have 2 pts, nice-to-have 1; met full, partial half, missing 0). Apply if 75%+ and no deal-breakers.

Every run is stored in SQLite and traced in Langfuse (one trace per run, a span per step).

Key principle: the LLM only does what code cannot (reading messy text, matching requirements to evidence). Rules, math and the verdict are plain Python so they are testable and deterministic.

## Data models

```python
class Requirement(BaseModel):
    text: str
    options: list[str]  # "Python or Go" -> ["Python", "Go"]


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


class RequirementMatch(BaseModel):
    requirement: str
    status: Literal["met", "partial", "missing"]
    evidence: str | None  # required unless missing


class Evaluation(BaseModel):
    verdict: Literal["apply", "skip"]
    match_pct: int
    deal_breakers: list[str]
    matches: list[RequirementMatch]
    gaps: list[str]
    highlights: list[str]
    prompt_version: str
    trace_id: str
```

SQLite `runs` table: id, created_at, source_url, job_text_hash, model, prompt_version, evaluation_json, cost_usd, latency_ms, trace_id, my_label.

## Stack

- Python 3.15 (`uv python install 3.15`), uv, ruff, mypy, pytest
- FastAPI + Typer
- Gemini API free tier via `google-genai` (key from aistudio.google.com), wrapped in `llm.py` so the provider can be swapped
- Pydantic v2
- httpx + trafilatura (or selectolax)
- SQLite
- Langfuse (free cloud plan) for traces, scores and datasets
- Secrets only in `.env` (never committed); job page text is data, never instructions to the agent

## Project layout

```
jobfit-agent/
  CLAUDE.md
  LEARNING.md
  docs/spec.md
  pyproject.toml
  .env.example
  profile.yaml            # my skills, facts and job rules
  prompts/
    extract_v1.md
    score_v1.md
  jobfit/
    api.py  cli.py  agent.py  fetch.py  llm.py
    rules.py  scoring.py  models.py  store.py  eval.py
  evals/jobs.jsonl
  tests/
```

## Evaluation targets (v1)

| Metric | Target |
| --- | --- |
| Verdict agreement with my labels (15 jobs) | 12/15 or better |
| False Apply | 1 or fewer |
| Requirement extraction recall | 80%+ |
| Evidence present for every "met" | 100% |
| Same verdict across 3 repeated runs | 14/15 or better |

## Milestones

- [ ] M1 Skeleton: repo, uv, ruff, pytest, `.env`, `profile.yaml`, models, one Gemini call returning a `JobPost` from pasted text
- [ ] M2 End to end: hard rules + scoring + verdict from the CLI; unit tests for rules and scoring
- [ ] M3 Tracing: Langfuse on every step; check one trace's cost and latency
- [ ] M4 Eval set: label 15 job posts in `evals/jobs.jsonl`; `python -m jobfit.eval`; record the first numbers
- [ ] M5 Improve: fix the top failure, bump prompt version, rerun eval, compare
- [ ] M6 Inputs and storage: URL fetch, SQLite history, FastAPI endpoint, agree/disagree feedback
- [ ] M7 Video prep: README with diagram; rehearse the 5-minute walkthrough

## My profile (source for profile.yaml)

- Abdul Wajed Khan, backend engineer, Dhaka, Bangladesh (UTC+6), 3.5+ years since Dec 2022
- Softwrd Limited (Placepoint group, Norway), Dec 2024 - present, remote: Go (Echo) service layer normalising legacy microservice APIs; GraphQL APIs and observability; now on the Hjemla team as an AI-assisted backend engineer in C#; used MongoDB with AI help
- Repliq Limited, Dec 2022 - Nov 2024: Django/DRF/PostgreSQL; fixed invoice race condition (atomic transactions, select_for_update); stock/history table redesign; N+1 fixes with indexing and Redis; sole backend engineer on a ~5,000-user system; led a 7-person team; TDD; Celery
- Skills: Python, Go, SQL, TypeScript/JavaScript, C# (working); Django, DRF, FastAPI, GraphQL, REST, Echo, Celery; PostgreSQL, MySQL, Redis, MongoDB; AWS (EC2, RDS), Docker, CI/CD, Nginx, DigitalOcean
- Not claimed: professional Kubernetes (hobby only), Java, Kotlin, Kafka, gRPC, Terraform, GCP, Spark
- Job rules: remote roles open to someone in Bangladesh, or relocation only with visa/relocation support stated; 75%+ match cutoff; a years-of-experience ask above mine is not a deal-breaker on its own
