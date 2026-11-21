# Progress

Where JobFit Agent stands, so a new chat can pick up from here. Update this at the end of every session.

Last updated: 2026-11-21 (session 1)

## How we work

- **Build simple, then add.** Start with the smallest thing that works, use it, see what breaks, add one piece to fix that one problem. Every piece needs a reason I saw myself.
- **Learn, build, break, fix, log.** After something works, break it on purpose. Log every failure in `LEARNING.md` (short format: what happened, why, what I did, what I learned).
- **Reproduce before fixing.** Don't fix something I can't measure yet (see #11).
- **Explain simply, one idea at a time.** When I said "I don't understand anything", going back to the 5 steps I do by hand worked.
- **Claude never commits.** It only gives me the commit message and commands.
- No em dashes in text written for me.

## Where we are

Not following the M1 to M7 milestones strictly. Using the "build simple, then add" ladder instead:

- [x] **v0:** one file, job text + profile to Gemini, prints apply/skip as free text
- [x] **Step 1: structured output** (in progress, working): Gemini fills a `JobPost` form, Pydantic validates it
  - [x] model fallback + timeouts in `llm.py`
  - [x] run log in `runs/*.json`
  - [ ] break tests: same job 3 runs, prompt injection, validation failure
- [ ] **Step 2: deal-breaker rules in plain Python** (`rules.py`) + first unit tests
- [ ] Step 3: match % in Python (needs scoring + `profile.yaml`)
- [ ] Step 4: eval set of 15 labeled jobs
- [ ] Step 5: Langfuse tracing (replaces the hand-made run log)
- [ ] Step 6: URL fetch + cleaning, SQLite, API
- [ ] Later (M8): scheduled search with Kafka (I want to learn Kafka; it fits here, not in v1)

## What's built

Flat files for now (not yet the `jobfit/` package layout from the spec):

| File | What it does |
| --- | --- |
| `models.py` | `Requirement` (text + options) and `JobPost` (title, company, location, work_mode, open_to_bd, visa_support, years_required, must_haves, nice_to_haves, salary). Title and company must be non-empty. |
| `llm.py` | `generate_json(prompt, schema)`: tries `MODELS` in order (3.6-flash, 3.5-flash, 3.5-flash-lite). SDK retries off, 30 s timeout per call. Falls back on 5xx, 429 and `httpx2.TransportError`. Raises on other 4xx (my bugs). Returns response, model used, attempts. Raises `AllModelsFailed`. |
| `main.py` | Reads `job.txt`, builds the extraction prompt, calls `generate_json`, saves the run to `runs/` (before validating), validates with Pydantic, prints the JSON. |
| `try_models.py` | Lists the models my key can see and sends a tiny prompt to each to check which answer. |
| `LEARNING.md` | 12 failure entries + 5 big lessons at the top. |
| `docs/spec.md`, `CLAUDE.md`, `README.md` | Spec, working rules, public README. |

Not in git: `.env` (API key), `job.txt` (copied job post), `runs/` (logs with job text).

## Key decisions so far

- LLM only does what code can't (reading the post, matching evidence). Rules, math and verdict in Python.
- Field names: `open_to_bd`, `must_haves`, `nice_to_haves`. Code and docs must match.
- Log the exact prompt sent, before validating, so I can see what the model really got.
- Python 3.15.2, uv 0.13+ (old uv only knew 3.15 beta).
- Gemini free tier. 3.7 and 3.8 flash were overloaded today; 3.6-flash is first in the list.
- Don't add more fallback models without testing they answer and extract well. Real fix for slowness is a total time budget per run.
- Repo is public: no job post text, no logs, no secrets in git.

## Open questions

- **For step 2:** if a job doesn't say whether it's open to Bangladesh (`open_to_bd` is null), what should the rules do? Skip, apply, or flag for me? I need to answer this before building `rules.py`.
- Time budget: limit per model vs total limit per run (spec: under 30 s).
- Soft skills as must-haves ("Empathy", "Curious mindset"): decide during scoring.
- "And" read as "or" in `options` (#11): fix when scoring exists and can show it.

## Gotchas

- The Gemini SDK uses `httpx2`, not `httpx`. Catch `httpx2` errors (#12).
- A model being listed doesn't mean I can call it (2.5-flash gave 404).
- The same 30 s timeout can come back as a 504 from Google or a `ReadTimeout` on my side.
- Copying a job page can pick up browser extension text (Simplify). Check `job.txt`.

## Next session, in order

1. Run the 3 break tests from step 1 and log what I find.
2. Optional: test `gemini-3.1-flash-lite` and `gemini-2.5-flash-lite` as a last-resort fallback (must answer AND extract well).
3. Answer the `open_to_bd = null` question.
4. Start step 2: `rules.py` + first pytest tests.
