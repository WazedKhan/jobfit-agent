import time

import httpx2
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

# triable models, first one gets priority
MODELS = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]

client = genai.Client(
    http_options=types.HttpOptions(
        timeout=30_000,  # 30_000 == 30s, gives up on the call after 30s
        retry_options=types.HttpRetryOptions(
            attempts=1
        ),  # this will make sure google client doesn't attempt more then 1
    )
)


class AllModelsFailed(Exception):
    """Every model in MODELS failed with a temporary error"""


def generate_json(prompt: str, schema: type[BaseModel]):
    attempts = []
    for model in MODELS:
        start = time.perf_counter()
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0,
                ),
            )
        except errors.ServerError as se:
            attempts.append(
                {"model": model, "error": f"{se.code} {se.status}", "ms": _ms(start)}
            )
            continue
        except errors.ClientError as ce:
            if ce.code == 429:
                attempts.append(
                    {"model": model, "error": "429 rate limited", "ms": _ms(start)}
                )
                continue
            raise
        except (
            httpx2.TransportError
        ) as te:  # timeouts, dropped connections, DNS failures
            attempts.append(
                {"model": model, "error": type(te).__name__, "ms": _ms(start)}
            )
            continue

        attempts.append({"model": model, "ok": True, "ms": _ms(start)})
        return response, model, attempts

    raise AllModelsFailed(attempts)


def _ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)
