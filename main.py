import json
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()  # reads GEMINI_API_KEY from .env

from llm import AllModelsFailed, generate_json
from models import JobPost

job_post = Path("job.txt").read_text(encoding="utf-8")
PROMPT_VERSION = "extract_v2"
template = Path(f"prompts/{PROMPT_VERSION}.md").read_text(encoding="utf-8")
prompt = template.replace("{job_post}", job_post)


def save_run(run: dict) -> None:
    Path("runs").mkdir(exist_ok=True)
    path = Path("runs") / f"{datetime.now():%Y%m%d-%H%M%S}.json"
    path.write_text(json.dumps(run, indent=2, ensure_ascii=False))
    print(f"Logged to {path}")


run: dict[str, Any] = {
    "time": datetime.now().isoformat(timespec="seconds"),
    "prompt_version": PROMPT_VERSION,
    "prompt": prompt,
}

try:
    response, model, attempts = generate_json(prompt, JobPost)
except AllModelsFailed as e:
    run["attempts"] = e.args[0]
    save_run(run)
    raise SystemExit("all models are busy right now. try again in few minutes")

usage = response.usage_metadata  # can be None
run.update(
    model=model,
    attempts=attempts,
    raw_response=response.text,
    tokens_in=usage.prompt_token_count if usage else None,
    tokens_out=usage.candidates_token_count if usage else None,
)

save_run(run)
if response.text is None:
    raise SystemExit("model returned no text. see the run log")
job = JobPost.model_validate_json(response.text)
print(job.model_dump_json(indent=2))
