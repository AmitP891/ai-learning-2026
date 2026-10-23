"""Rule-based requirement quality checks, shared by the tool-use script and the MCP server."""
import csv
import os
import re

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "..", "claude-api", "sample_requirements.csv")

VAGUE = ["fast", "quick", "user-friendly", "easy", "adequate", "sufficient", "appropriate",
         "typical", "reasonable", "efficient", "flexible", "robust", "as needed", "etc"]


def load_requirements(csv_path=SAMPLE_CSV):
    with open(csv_path, newline="") as f:
        return {row["id"]: row["text"] for row in csv.DictReader(f)}


def list_requirements(csv_path=SAMPLE_CSV):
    return [{"id": k, "text": v} for k, v in load_requirements(csv_path).items()]


def check_requirement(req_id, csv_path=SAMPLE_CSV):
    reqs = load_requirements(csv_path)
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
    else:
        # check each 'shall' clause on its own, so one number can't cover for another clause
        clauses = [c.strip(" ,.") for c in re.split(r"\band\s+(?=shall\b)", text, flags=re.I)]
        if len(clauses) > 1:
            for c in clauses:
                if not re.search(r"\d", c):
                    issues.append(f"Clause has no measurable value: '{c}'")
    return {"id": req_id, "text": text, "verdict": "PASS" if not issues else "REVIEW", "issues": issues}
