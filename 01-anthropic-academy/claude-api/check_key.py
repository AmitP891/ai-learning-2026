"""Check that your Anthropic API key works before running the other scripts.

Run:  python3 check_key.py
"""
import os

import anthropic
from dotenv import dotenv_values, find_dotenv, load_dotenv

shell_key = os.environ.get("ANTHROPIC_API_KEY", "")
env_path = find_dotenv(usecwd=True) or find_dotenv()
file_key = (dotenv_values(env_path).get("ANTHROPIC_API_KEY") or "") if env_path else ""
tail = lambda k: f"...{k[-4:]}" if k else "(none)"
print("Diagnostics (only the last 4 characters of each key are shown):")
print(f"  .env file used : {env_path or 'NOT FOUND'}")
print(f"  key in .env    : {tail(file_key)}")
print(f"  key in shell   : {tail(shell_key)}")
load_dotenv(env_path, override=True) if env_path else None
raw = os.environ.get("ANTHROPIC_API_KEY", "")
key = raw.strip().strip("\"'\u201c\u201d\u2018\u2019")
if key != raw:
    print("  note           : removed stray quotes or spaces around the key")
print(f"  key being used : {tail(key)}\n")

if not key:
    print("No key found. Add it to a .env file (see .env.example) or run: export ANTHROPIC_API_KEY=...")
    raise SystemExit(1)

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
