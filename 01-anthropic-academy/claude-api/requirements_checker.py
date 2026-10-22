"""Requirements quality checker: Claude + tool use.

Anthropic Academy, Building with the Claude API, section 4 (Tool use).
Claude reviews a set of (synthetic) system requirements. It can't read the file
or apply the rules itself, so it calls two Python tools:

  list_requirements()          -> every requirement in the CSV
  check_requirement(req_id)    -> rule-based checks on one requirement

Then it writes a review with suggested rewrites.

Run:  python3 requirements_checker.py                 (uses sample_requirements.csv)
      python3 requirements_checker.py my_reqs.csv
"""
import csv
import json
import os
import re
import sys

import anthropic
from dotenv import load_dotenv

load_dotenv(override=True)
os.environ["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY", "").strip().strip("\"'“”‘’")

client = anthropic.Anthropic()
MODEL = "claude-sonnet-5-5"
CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "sample_requirements.csv")

# ---------- the tools (plain Python) ----------

VAGUE = ["fast", "quick", "user-friendly", "easy", "adequate", "sufficient", "appropriate",
         "typical", "reasonable", "efficient", "flexible", "robust", "as needed", "etc"]


def load_requirements():
    with open(CSV_PATH, newline="") as f:
        return {row["id"]: row["text"] for row in csv.DictReader(f)}


def list_requirements():
    return [{"id": k, "text": v} for k, v in load_requirements().items()]


def check_requirement(req_id):
    reqs = load_requirements()
    if req_id not in reqs:
        return {"error": f"No requirement with id {req_id}"}
    text = reqs[req_id]
    low = text.lower()
    issues = []
    if not re.search(r"\bshall\b", low):
        weak = [m for m in ("should", "may", "will", "can") if re.search(rf"\b{m}\b", low)]
        issues.append(f"Weak or missing modal verb ({', '.join(weak) or 'none'}); use 'shall'")
    vague = [w for w in VAGUE if re.search(rf"\b{re.escape(w)}\b", low)]
    if vague:
        issues.append(f"Vague, untestable wording: {', '.join(vague)}")
    if re.search(r"\b(tbd|tbc|tba)\b", low):
        issues.append("Contains TBD/TBC: the requirement is incomplete")
    if len(re.findall(r"\bshall\b", low)) > 1:
        issues.append("More than one 'shall': split into separate requirements")
    if not re.search(r"\d", text):
        issues.append("No measurable value (number + unit), so it can't be verified")
    return {"id": req_id, "text": text, "verdict": "PASS" if not issues else "REVIEW", "issues": issues}


TOOLS = [
    {
        "name": "list_requirements",
        "description": "Return every requirement in the requirements file, as a list of {id, text}.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "check_requirement",
        "description": "Run rule-based quality checks on one requirement (modal verb, vague wording, "
                       "TBD, compound statements, measurability). Returns a verdict and a list of issues.",
        "input_schema": {
            "type": "object",
            "properties": {"req_id": {"type": "string", "description": "Requirement id, e.g. REQ-002"}},
            "required": ["req_id"],
        },
    },
]


def run_tool(name, args):
    if name == "list_requirements":
        return list_requirements()
    if name == "check_requirement":
        return check_requirement(args["req_id"])
    return {"error": f"Unknown tool {name}"}


# ---------- the agent loop ----------

SYSTEM = """You are a systems engineering requirements reviewer.
Use the tools: list the requirements, then check every one of them. Do not judge them yourself without the tool.
Then reply with:
1. A one-line summary: how many passed and how many need review.
2. For each requirement that needs review: the id, the main issue in a few words, and a rewritten,
   testable version using 'shall' and a measurable value. Where you must invent a number, mark it [assumed].
Keep the whole reply under 250 words. Plain text, no tables."""


def main():
    print(f"Reviewing {CSV_PATH}\n")
    messages = [{"role": "user", "content": "Review all the requirements in the file."}]
    while True:
        response = client.messages.create(
            model=MODEL, max_tokens=4000, system=SYSTEM, tools=TOOLS, messages=messages)
        # keep the full content (including any thinking blocks) in the history
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            break
        results = []
        for block in response.content:
            if block.type == "tool_use":
                out = run_tool(block.name, block.input)
                arg = block.input.get("req_id", "")
                tag = f"  -> {out.get('verdict')}" if isinstance(out, dict) and "verdict" in out else ""
                print(f"[tool] Claude called {block.name}({arg}){tag}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(out)})
        messages.append({"role": "user", "content": results})
    print("\n" + "".join(b.text for b in response.content if b.type == "text").strip())


if __name__ == "__main__":
    main()
