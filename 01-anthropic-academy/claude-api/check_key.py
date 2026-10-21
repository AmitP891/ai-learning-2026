"""Check that your Anthropic API key works before running the other scripts.

Run:  python3 check_key.py
"""
import os

import anthropic
from dotenv import load_dotenv

load_dotenv(override=True)
key = os.environ.get("ANTHROPIC_API_KEY", "")

if not key:
    print("No key found. Add it to a .env file (see .env.example) or run: export ANTHROPIC_API_KEY=...")
    raise SystemExit(1)

print(f"Key found: {key[:10]}...{key[-4:]}  (only the start and end are shown)")
try:
    r = anthropic.Anthropic(api_key=key).messages.create(
        model="claude-haiku-5-5", max_tokens=200,
        messages=[{"role": "user", "content": "Reply with just: OK"}])
    text = "".join(b.text for b in r.content if b.type == "text").strip()
    print(f"Success! Claude replied: {text}")
except anthropic.AuthenticationError:
    print("The key was rejected. Check you copied the whole key with no spaces, and that it hasn't been deleted.")
except anthropic.PermissionDeniedError:
    print("The key works but lacks permission. Check the key's workspace in the Console.")
except anthropic.RateLimitError:
    print("Rate limited or out of credit. Check Plans & Billing in the Console.")
except anthropic.APIStatusError as e:
    print(f"API error {e.status_code}: {e.message}")
except anthropic.APIConnectionError:
    print("Couldn't reach the API. Check your internet connection.")
