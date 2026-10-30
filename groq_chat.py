import os
import sys
from pathlib import Path

from groq import Groq


env_file = Path(__file__).with_name(".env")
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        name, separator, value = line.partition("=")
        if separator and name.strip() == "GROQ_API_KEY":
            os.environ.setdefault("GROQ_API_KEY", value.strip().strip("\"'"))

api_key = os.environ.get("GROQ_API_KEY", "").strip()
if not api_key:
    raise SystemExit("Add your Groq API key to .env as GROQ_API_KEY= and run again.")

client = Groq(api_key=api_key)
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Say hello in Kannada in one short sentence."}],
)

sys.stdout.reconfigure(encoding="utf-8")
print(response.choices[0].message.content)
