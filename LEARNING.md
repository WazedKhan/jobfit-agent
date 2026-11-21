# Learning log

One entry per thing that broke, plus a short note at the end of each milestone. This is the raw material for the Evaboot video and for interview answers.

## How to write an entry

One failure per entry. Write it right after it happens, while the details are fresh.

```
### <date> · <step> · <short name of the failure>
- What broke: the symptom I saw, with the exact output or error
- How I found it: the test, trace, log line or comparison that showed it
- Root cause: why it happened (check what the model actually received before blaming it)
- Fix: what I changed (file, prompt version), or "planned: <step>" if not fixed yet
- Regression test: the test that now guards it, or "planned: <test idea>"
- Interview line: one or two sentences I would say about it
```

## Planned failures to trigger

- [ ] M1: LLM returns JSON that fails Pydantic validation
- [ ] M1: enum casing ("Remote" vs "remote")
- [ ] M1: Gemini free tier 429 rate limit
- [ ] M1: prompt injection inside the job post text
- [ ] M2: 74.5% rounding at the 75% cutoff
- [ ] M2: `None` (not stated) treated as `False`
- [ ] M2: "Python or Go" counted as two requirements
- [ ] M3: spans missing when a step raises
- [ ] M3: CLI exits before Langfuse flushes
- [ ] M3: cost shows $0
- [ ] M4: different verdicts for the same post across runs
- [ ] M5: prompt fix that passes one case and breaks others
- [ ] M6: blocked fetch, JavaScript-only page, timeout

## Entries

### 2026-11-21 · v0 · Busy Gemini models return 503
- What broke: my first call to `gemini-3.8-flash` crashed with `503 UNAVAILABLE: This model is currently experiencing high demand`. Switching to `gemini-3.7-flash` gave the same error.
- How I found it: read the last line of the traceback. Then I wrote `try_models.py` to send a tiny prompt to each model one by one instead of guessing.
- Root cause: Google's servers for the newest models were overloaded. My code and my key were fine: 3.6-flash, 3.5-flash and 3.5-flash-lite all answered. 2.5-flash showed up in `models.list()` but returned 404 when I called it. The SDK also retried the busy models silently, so the test took 53 seconds.
- Fix: switched `main.py` to `gemini-3.6-flash`. Planned for `llm.py`: a fallback list of models, try the next one on 503, with a timeout so hidden retries cannot make a run slow.
- Regression test: planned. `test_llm_falls_back_on_503`: a fake client that returns 503 for the first model must make `llm.py` use the second one.
- Interview line: "External APIs fail. I tested each model one by one instead of guessing, and learned that a model being listed doesn't mean I can call it. That's why my LLM wrapper has a fallback list and a timeout."

### 2026-11-21 · v0 · Confident verdict about a page it never read
- What broke: with only the Wolt job URL in the prompt, Gemini answered APPLY and claimed Wolt "routinely provides full visa sponsorship". With the real job text, the same job got SKIP.
- How I found it: I ran the same job twice, once as a URL and once as the pasted text, and compared the verdicts.
- Root cause: the LLM cannot open links. It guessed from general knowledge about Wolt and never said it was missing information.
- Fix: planned for the fetch step. Download the page and stop with a clear error if the text is empty or too short.
- Regression test: planned. `test_url_only_input_raises_error`: a URL-only or empty input must raise an error, never return a verdict.
- Interview line: "The model never says 'I don't know'. My code has to guarantee it gets the right input before I trust the output."

### 2026-11-21 · v0 · Junk text from a browser extension changed the verdict
- What broke: with the real job text, Gemini gave "low automated resume match score" as one reason to skip. I first thought it invented the score.
- How I found it: while debugging step 1, I opened `job.txt` and found Simplify's widget text at the top ("1 out of 5 keywords matched", "20", "Low Match"). I had copied it from the page together with the job post.
- Root cause: dirty input, not hallucination. The model used text that really was in the prompt. It just wasn't part of the job post.
- Fix: removed the widget text from `job.txt` by hand. Planned for the fetch step: clean the page to the job post only (trafilatura), and tell the model to use only the job post content.
- Regression test: planned. An eval case with extra non-job text (banners, widgets) that must not change the extracted fields or the verdict.
- Interview line: "I blamed the model for inventing a score, but the score was in my input, copied from a browser extension. Real inputs are noisy, so cleaning them is part of the agent, not an afterthought."

### 2026-11-21 · v0 · Nice-to-have treated as a must-have
- What broke: Gemini said the role "heavily targets" Spark and Flink and used that as a main reason to skip. The post only says "ideally some exposure to distributed compute (e.g. Spark, Flink)".
- How I found it: I checked the claim against the actual qualifications in the Wolt post.
- Root cause: the prompt didn't ask the model to separate must-haves from nice-to-haves, so it weighed every skill it saw the same way.
- Fix: planned for the structured output step. `JobPost` has separate `must_haves` and `nice_to_haves` lists, and scoring gives must-haves 2 points and nice-to-haves 1.
- Regression test: planned. An eval case using this Wolt post, where Spark and Flink must land in `nice_to_haves`.
- Interview line: "Words like 'ideally' change how much a skill matters. I made the model separate must-haves from nice-to-haves, and the weighting happens in code."

### 2026-11-21 · v0 · Rule missing from the prompt
- What broke: Gemini used my 3.5 years of experience as a main reason to skip a senior role. My rule is that years of experience alone is not a deal-breaker.
- How I found it: I first thought the model ignored my rule. Then I checked `MY_PROFILE` in `main.py`. The years rule was never in it; only the remote and visa rule was.
- Root cause: my bug, not the model's. It never received the rule, so it used its own judgment.
- Fix: planned. Move all my rules into `profile.yaml` as the single source, and check deal-breakers in plain Python (`rules.py`) so they don't depend on the model reading them.
- Regression test: planned. `test_years_above_mine_is_not_deal_breaker`: a job asking for more years than I have must not be skipped for that reason alone.
- Interview line: "Before blaming the model, I check what it actually received. This 'the model ignored my rule' bug turned out to be 'I never gave it the rule'."

## Milestone notes

### M1
_What I learned:_
