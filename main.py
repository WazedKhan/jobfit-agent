from dotenv import load_dotenv
from google import genai
from google.genai import types

from models import JobPost

load_dotenv()  # reads GEMINI_API_KEY from .env
client = genai.Client()  # picks up the key automatically

job_post = open("job.txt").read()

prompt = f"""Read this job post and fill in the fields.
Rules:
- Only use information written in the post, if something is not stated, use null.
- must_have: things the post requires, nice_to_have: words like "ideally", "bonus", "plus", "nice to have".
- If a requirement offers choices ("Python or Go"), list them in options.

Job Post:
{job_post}"""

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",  # response/answer will be in json format
        response_schema=JobPost,
        temperature=0,
    ),
)

job = JobPost.model_validate_json(response.text)
print(job.model_dump_json(indent=2))
