from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

# 1. Which models can my key use?
print("Models my key can see:")
for m in client.models.list():
    if "flash" in m.name:
        print("  ", m.name)

# 2. Which ones answer right now?
candidates = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
]

print("\nTrying each with a tiny prompt:")
for model in candidates:
    try:
        r = client.models.generate_content(model=model, contents="Say hi in 2 words.")
        print(f"  OK    {model}: {r.text.strip()}")
    except Exception as e:  # noqa: BLE001
        print(f"  FAIL  {model}: {str(e)[:80]}")
