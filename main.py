import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads GEMINI_API_KEY from .env

from llm import AllModelsFailed, generate_json
from models import JobPost

job_post = Path("job.txt").read_text(encoding="utf-8")

prompt = f"""Read this job post and fill in the fields.
Rules:
- Only use information written in the post, if something is not stated, use null.
- must_haves: things the post requires, nice_to_haves: words like "ideally", "bonus", "plus", "nice to have".
- If a requirement offers choices ("Python or Go"), list them in options.

Job Post:
{job_post}"""


def save_run(run: dict) -> None:
    Path("runs").mkdir(exist_ok=True)
    path = Path("runs") / f"{datetime.now():%Y%m%d-%H%M%S}.json"
    path.write_text(json.dumps(run, indent=2, ensure_ascii=False))
    print(f"Logged to {path}")


run = {"time": datetime.now().isoformat(timespec="seconds"), "prompt": prompt}

try:
    response, model, attempts = generate_json(prompt, JobPost)
except AllModelsFailed as e:
    run["attempts"] = e.args[0]
    save_run(run)
    raise SystemExit("all models are busy right now. try again in few minutes")

run.update(
    model=model,
    attempts=attempts,
    raw_response=response.text,
    tokens_in=response.usage_metadata.prompt_token_count,
    tokens_out=response.usage_metadata.candidates_token_count,
)

save_run(run)
job = JobPost.model_validate_json(response.text)
print(job.model_dump_json(indent=2))
