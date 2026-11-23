# Progress

The single source of truth for where JobFit Agent stands. A new chat reads this first, before suggesting anything.

Last updated: 2026-11-23 (session 3)

## The goal (does not change)

Build a small agent that reads a job post and says Apply or Skip, with a match %, gaps and resume highlights. Then **measure it** and show it in a **5-minute video for Evaboot** (agentic-workflows engineer role).

The video needs four things, so the project is done when I have them:

1. **Architecture and why:** works end to end (extract, rules, score, decide).
2. **How I observe and judge quality:** a Langfuse trace + real eval numbers on 15 labeled jobs.
3. **Problems I faced:** real failures from `LEARNING.md` and how a fix changed the numbers.
4. **What I learned / still figuring out.**

Anything that doesn't move one of these forward goes in the parking lot, not into today's work.

## Rules for Claude (anti-drift)

1. **Before suggesting anything,** read this file, `git log --oneline | head`, and the newest entries in `LEARNING.md`. If git or `LEARNING.md` is newer than "Last updated" above, this file is stale: update it first.
2. **Work only on the "Now" item below.** If something else comes up (a bug, an idea, a cool test), add it to the parking lot with one line and go back to "Now".
3. **Before proposing a test or feature, ask:** does this get me closer to the video? If not, park it.
4. **Don't redo work that's already logged.** Check `LEARNING.md` entry titles before suggesting a break test.
5. **At the end of every session,** update this file (where we are, decisions, session log, next) and give me the commit commands. Claude never commits.
6. **Don't guess. Check the code first.** Before suggesting a change, read the actual files involved (and `git status` / `git diff`). Never describe code, field names or behaviour from memory or from this file alone.
7. **Decisions are mine.** Claude can lay out options and trade-offs, but doesn't pick for me or write a decision into this file until I've said it. If Claude made a call to keep work moving, it says so and marks it "Claude's suggestion, not confirmed".
8. **Always fetch the latest docs before using a library.** Before writing or suggesting code that uses a library (google-genai, Pydantic, pytest, Langfuse, httpx, FastAPI, ...), look up its current official docs for the installed version (`uv.lock`). Don't rely on remembered APIs.
9. Follow `CLAUDE.md`: one step at a time, explain the concept first, I write the agent logic, no em dashes.

## Critical path to the video

| # | Step | Spec milestone | Status |
| --- | --- | --- | --- |
| 0 | v0: job text to Gemini, free-text apply/skip | | done |
| 1 | Structured output: `JobPost` + Pydantic, fallback, run log | M1 | done (break tests #13 to #16) |
| 2 | Deal-breaker rules in Python (`rules.py`) + first pytest tests | M2 | **now** |
| 3 | Scoring (LLM) + match % and verdict in Python, `profile.yaml` | M2 | next |
| 4 | Eval set: 15 labeled jobs, `eval` command, first real numbers | M4 | |
| 5 | Langfuse tracing (replaces the hand-made run log) | M3 | |
| 6 | Improve: fix the top eval failure, bump prompt version, rerun | M5 | |
| 7 | Video prep: README diagram, rehearse twice | M7 | |
| 8 | Nice to have: URL fetch, SQLite, FastAPI | M6 | only if time |

Spec M1 to M7 is the reference. I follow this ladder, which builds the same things in a "simple first, add when needed" order.

## Now

**Step 2: `rules.py`.**

1. Put `MODELS` in `llm.py` back to the full list (it's set to 3.6-flash only for break test #16; not committed).
2. Decide: what do the rules do when `open_to_bd` or `visa_support` is `null` (not stated)? Skip, apply, or flag? This must be answered before writing code.
3. Claude explains the concept + asks 2 or 3 check questions. Then I write `rules.py` and pytest tests.

## What's built

Flat files for now (not yet the `jobfit/` package layout from the spec):

| File | What it does |
| --- | --- |
| `models.py` | `Requirement` (text + options) and `JobPost` (title, company, location, work_mode, open_to_bd, visa_support, years_required, must_haves, nice_to_haves, salary). Title and company must be non-empty. |
| `llm.py` | `generate_json(prompt, schema)`: tries `MODELS` in order (3.6-flash, 3.5-flash, 3.5-flash-lite). SDK retries off, 30 s timeout per call. Falls back on 5xx, 429 and `httpx2.TransportError`. Raises on other 4xx (my bugs). Returns response, model used, attempts. Raises `AllModelsFailed`. |
| `main.py` | Reads `job.txt`, builds the extraction prompt (inline, not yet in `prompts/`), calls `generate_json`, saves the run to `runs/` before validating, validates with Pydantic, prints the JSON. |
| `try_models.py` | Lists the models my key can see and sends a tiny prompt to each. |
| `LEARNING.md` | 16 failure entries + 5 big lessons at the top. |
| `docs/spec.md`, `CLAUDE.md`, `README.md` | Spec, working rules, public README. |

Not built yet from spec M1: `profile.yaml`, `tests/`, `prompts/extract_v1.md`. Add each when a step needs it (tests in step 2, profile in step 3).

Not in git: `.env`, `job.txt`, `job.clean.txt`, `runs/`.

## Decisions (with date)

- 2026-11-21: LLM only does what code can't (reading the post, matching evidence). Rules, math and verdict in Python.
- 2026-11-21: field names `open_to_bd`, `must_haves`, `nice_to_haves`. Code and docs must match.
- 2026-11-21: log the exact prompt sent, before validating.
- 2026-11-21: Python 3.15.2, uv 0.13+. Gemini free tier, 3.6-flash first in the list.
- 2026-11-21: don't add fallback models without testing they answer and extract well.
- 2026-11-21: repo is public. No job text, no logs, no secrets in git.
- 2026-11-23: don't fix things I can't measure yet. Extraction issues (wording drift, `work_mode` guessing, and/or in options) wait for the eval set.
- 2026-11-23: break tests stop at step 1. Validation-failure test moved to the parking lot so step 2 can start. (Claude's suggestion, not confirmed.)

## Open questions

- **Blocking step 2:** what to do when `open_to_bd` / `visa_support` is `null`.
- Time budget: per model vs total per run. Data: normal calls take 18 to 27 s against a 30 s limit (#16); worst run took 63 s (#15).
- Soft skills as must-haves ("Empathy", "Curious mindset"): decide in step 3.

## Parking lot (noticed, not now)

Each item says when it comes back.

- Validation-failure break test: when the spec's "retry once on validation failure" is added.
- `work_mode` has no `null`, so the model guesses ("onsite" for Wolt, #16): measure in step 4 eval, then decide.
- Requirement wording and `options` drift between runs (#13, #16): eval matching must not use exact strings (step 4).
- "And" read as "or" in `options` (#11), `options` undefined for single requirements (#15): fix in step 3 when scoring can show the effect.
- Prompt injection works on 3.5-flash-lite (#14): fix in step 6 (Improve), with a regression case in the eval set.
- Total time budget per run: decide before step 5.
- Test `gemini-3.1-flash-lite` / `gemini-2.5-flash-lite` as last-resort fallback: optional, only if outages block work.
- Kafka scheduled search (I want to learn Kafka): after the video, not in v1.

## Gotchas

- The Gemini SDK uses `httpx2`, not `httpx`. Catch `httpx2` errors (#12).
- A listed model may still 404 (2.5-flash).
- The same 30 s timeout can come back as a 504 from Google or a `ReadTimeout` on my side.
- Copying a job page can pick up browser extension text (Simplify). Check `job.txt`.

## Session log

- 2026-11-21 (session 1): v0, structured output, fallback + timeouts, run log, `LEARNING.md` #1 to #12.
- 2026-11-22 (session 2): break tests: same job 3 runs (#13), prompt injection (#14), timeout changes output shape (#15). This file wasn't updated, which caused session 3 to repeat a test.
- 2026-11-23 (session 3): reran the same-job test on one model (#16: consistent is not correct). Rewrote this file to stop drift. Next: step 2.
