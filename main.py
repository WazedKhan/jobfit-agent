from dotenv import load_dotenv
from google import genai

load_dotenv()                      # reads GEMINI_API_KEY from .env
client = genai.Client()            # picks up the key automatically

MY_PROFILE = """
Backend engineer, 3.5 years, based in Dhaka, Bangladesh.
Python, Django, DRF, FastAPI, Go, PostgreSQL, Redis, Docker, AWS.
Rules: remote roles open to Bangladesh, or relocation with visa support.
"""

job_post = job_post = open("job.txt").read()

prompt = f"""Here is my profile:
{MY_PROFILE}

Here is a job post:
{job_post}

Should I apply? Answer APPLY or SKIP, then explain in 3 short lines."""

response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
print(response.text)
