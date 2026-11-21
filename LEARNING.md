# Learning log

One entry per thing that broke, plus a short note at the end of each milestone. This is the raw material for the Evaboot video and for interview answers.

## How to write an entry

```
### <milestone> · <short name of the failure>
- What broke: the symptom I saw (error, wrong verdict, missing span)
- How I found it: test, trace, log line, eval number
- Root cause: why it happened
- Fix: what I changed (file, prompt version)
- Regression test: test name that now guards it
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

_None yet._

## Milestone notes

### M1
_What I learned:_
