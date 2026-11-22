# Learning log

Short notes on what broke while building JobFit Agent, why, and what I did about it.
Written so I (or anyone) can read it in 5 minutes before an interview.

## Read this first: the 5 big lessons

1. **Check what the model received before blaming it.** Three of my "LLM bugs" were really my bugs (#3, #5, #6).
2. **The model never says "I don't know".** Give it a link it can't open and it still answers confidently (#2).
3. **A valid answer is not a correct answer.** The schema checks the shape, not the truth (#7).
4. **External APIs fail.** Plan for busy, slow and missing models, and make every attempt visible (#1, #8, #9).
5. **Let code do what code can do.** Rules, weights and the final decision go in Python, not in the prompt (#4, #5).

## How to write an entry

Keep it short. One problem per entry. Write it right after it happens.

```
### #N · Short name
- What happened: what I saw
- Why: the real cause
- What I did: the fix, or "planned: ..."
- What I learned: the lesson, in one sentence
```

## Entries

### #1 · Newest Gemini models were busy (503)
- **What happened:** `gemini-3.8-flash` and `3.7-flash` both failed with "503: high demand".
- **Why:** Google's servers were overloaded, not my code. I tested each model with a tiny prompt: 3.6, 3.5 and 3.5-lite worked. 2.5-flash was in the model list but gave 404.
- **What I did:** switched to 3.6-flash. Learned: "listed" doesn't mean "callable", so test it.
- **What I learned:** "I tested models one by one instead of guessing, and found that a listed model can still return 404."

### #2 · Confident answer about a page it never read
- **What happened:** I gave Gemini only the job URL. It said APPLY and claimed Wolt "routinely provides visa sponsorship". With the real text, the same job got SKIP.
- **Why:** the model can't open links. It guessed from what it knows about Wolt and didn't say it was missing information.
- **What I did:** planned: the fetch step downloads the page and stops with an error if the text is empty.
- **What I learned:** "The model never says 'I don't know', so my code makes sure it gets the right input."

### #3 · Junk text from a browser extension
- **What happened:** Gemini gave a "low resume match score" as a reason to skip. I thought it made the score up.
- **Why:** it didn't. The Simplify extension's widget ("Low Match 20") was in the text I copied.
- **What I did:** removed it by hand. Planned: the fetch step cleans the page down to the job post only.
- **What I learned:** "I blamed the model, but the bad data was in my input. Cleaning input is part of the agent."

### #4 · Nice-to-have treated as a must-have
- **What happened:** Gemini said the role "heavily targets" Spark and Flink. The post says "ideally some exposure".
- **Why:** my prompt didn't ask it to separate must-haves from nice-to-haves.
- **What I did:** the `JobPost` model now has separate `must_haves` and `nice_to_haves` lists. Fixed: Spark and Flink now land in `nice_to_haves`.
- **What I learned:** "Words like 'ideally' change how much a skill matters, so the model sorts them and code does the weighting."

### #5 · Rule missing from the prompt
- **What happened:** Gemini skipped a job mainly because of my 3.5 years of experience. My rule says years alone is not a deal-breaker.
- **Why:** I never put that rule in the prompt. The model didn't ignore it; it never got it.
- **What I did:** planned: rules live in `profile.yaml` and are checked in plain Python (`rules.py`).
- **What I learned:** "'The model ignored my rule' turned out to be 'I never gave it the rule'."

### #6 · Missing `f` sent a placeholder instead of the job
- **What happened:** Gemini returned an empty title and company and guessed "remote".
- **Why:** I forgot the `f` before the prompt string, so the model got the text `{job_post}`, not the job. This bug would break any LLM.
- **What I did:** added the `f`. Added a run log (`runs/*.json`) that saves the exact prompt, so I can see what the model got.
- **What I learned:** "I log the exact prompt on every run. That turned a confusing bug into a 10-second fix."

### #7 · Valid but empty answer
- **What happened:** with no job text (#6), the JSON still passed Pydantic validation.
- **Why:** an empty string is still a string. The schema guarantees the shape, not the truth.
- **What I did:** added `Field(min_length=1)` to `title` and `company`, so empty values now fail.
- **What I learned:** "Structured output gives you the right shape. You still need checks for the right content."

### #8 · Hidden retries made failures slow
- **What happened:** a failed call took over a minute before it crashed.
- **Why:** the Gemini SDK retried quietly in the background.
- **What I did:** built `llm.py`: SDK retries off, 30 s limit per call, a fallback list of models, and every attempt saved in the run log. 4xx errors (my bugs) stop right away instead of falling back.
- **What I learned:** "I turned off the hidden retries and handle failures myself, so every attempt is visible."

### #9 · All models failed, and the 504s were my own timeout
- **What happened:** 3.6 and 3.5 failed with 504 after about 29.7 s, 3.5-lite with 503. The whole run took about 61 s.
- **Why:** my 30 s limit is sent to Google as a deadline, so a slow model returns 504, not a timeout error. 503 means "busy, refused fast". 504 means "accepted, but too slow".
- **What I did:** kept the clean "all models busy" message. Open question: a time limit per model vs a total limit per run (spec says under 30 s).
- **What I learned:** "My fallback gives each model up to 30 s. With 3 models that can add up to 90 s, so I need a total time limit for the whole run, not just one per call."

### #10 · The fallback model gave a different answer
- **What happened:** 3.6 and 3.5 timed out, so 3.5-lite answered. Same job, but `options` was now filled in and the `text` was reworded instead of copied from the post.
- **Why:** a fallback swaps in a different (smaller) model, and each model reads the post a bit differently.
- **What I did:** the run log saves which model answered. Planned: run the eval set per model, so I know if a bad result came from my prompt or from a weaker model taking over.
- **What I learned:** A fallback makes the agent more reliable but less consistent. I always need to know which model produced the answer.

### #11 · "And" treated as "or" in options
- **What happened:** "Comfortable working with backend systems, APIs" came back with `options: ["backend systems", "APIs"]`, which means either one is enough. The post means both.
- **Why:** my prompt only explains `options` for "or" choices. It doesn't say what to do with "and" lists.
- **What I did:** not fixed yet, on purpose. Nothing uses `options` until scoring exists, so I can't measure the effect. Planned: when scoring is built, add a test case (someone with APIs but no backend systems must not get full points), watch it fail, then fix the prompt.
- **What I learned:** I noticed it early but waited until I could measure it. A fix I can't verify is just a guess.

### #12 · My timeout handler caught the wrong library's error
- **What happened:** a call timed out after 31 s and crashed with `httpx2.ReadTimeout`, even though `llm.py` had an `except httpx.TimeoutException`.
- **Why:** the Gemini SDK (3.6.1) sends requests with `httpx2`, but I caught errors from `httpx`. They are two different packages with different exception classes. Also, the same 30 s limit can fail two ways: a 504 from Google (#9) or a timeout on my side, depending on who gives up first.
- **What I did:** catch `httpx2.TransportError` instead. It covers timeouts, dropped connections and DNS failures, and the log records the exact error type.
- **What I learned:** Catch errors from the library that actually raises them, and prove a handler works by triggering the error, not by reading the code.

### #13 · Same job, 3 runs: structure stable, wording drifts
- **What happened:** I ran the Wolt job 3 times, all on `gemini-3.6-flash` with temperature at the default. Title, company, location, work_mode, the three nulls, salary, list counts (4 must-haves, 3 nice-to-haves) and every `options` list were identical. Only two nice-to-have `text` fields changed: "Background ideally in" / "Background in" / "Experience in", and run 2 dropped "(e.g. Spark, Flink)".
- **Why:** the model samples tokens, so the same input can give different output. It also paraphrases requirement text instead of copying it. Dropping "ideally" turns a soft wish into a harder ask.
- **What I did:** nothing yet, on purpose. No score exists to show the drift changes a verdict. Planned: if scoring shows it matters, tell the prompt to copy requirement text exactly, bump the prompt version and rerun the eval.
- **What I learned:** Same prompt doesn't mean same output. Fields copied straight from the post stay stable; fields where the model has to interpret text drift. One clean job on one model proves little, so the real stability number comes from the eval set (15 jobs x 3 runs).

## Planned failures to trigger

- [ ] LLM returns JSON that fails Pydantic validation
- [ ] Enum casing ("Remote" vs "remote")
- [ ] Gemini free tier 429 rate limit
- [ ] Prompt injection inside the job post text
- [ ] 74.5% rounding at the 75% cutoff
- [ ] `None` (not stated) treated as `False`
- [ ] "Python or Go" counted as two requirements
- [ ] Spans missing when a step raises
- [ ] CLI exits before Langfuse flushes
- [ ] Cost shows $0
- [ ] Different verdicts for the same post across runs
- [ ] Prompt fix that passes one case and breaks others
- [ ] Blocked fetch, JavaScript-only page, timeout
