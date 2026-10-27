"""Requirements checker MCP server, v2.

Anthropic Academy, MCP Advanced Topics. Built on v1 (requirements_server.py) with four upgrades:

  1. check_all          checks a whole CSV and sends PROGRESS notifications ("4/8 checked")
  2. fix_requirement    uses ELICITATION: the server pauses and asks YOU for the missing number,
                        so the rewrite uses a real value instead of one the AI made up
  3. Folder guard       only reads CSVs inside one allowed folder (the explicit replacement for roots)
  4. Two transports     stdio for Claude Code / Desktop, or streamable HTTP with --http

Note: the MCP spec of 2026-07-28 deprecated sampling, roots and protocol logging (SEP-2577).
They still work, but new servers shouldn't build on them, so v2 uses elicitation, a
configured folder and stderr logging instead.

Run:
  python3 requirements_server_v2.py            # stdio (Claude Code, Claude Desktop)
  python3 requirements_server_v2.py --http     # http://127.0.0.1:8000/mcp
"""
import logging
import os
import sys

from pydantic import BaseModel, Field

from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "shared"))
import requirements_rules as rules  # noqa: E402

# --- Logging: stderr, never stdout (stdout carries the MCP messages in stdio mode) ---
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("requirements-checker")

# --- Folder guard: CSVs may only come from this folder (or below it) ---
ALLOWED_DIR = os.path.realpath(os.environ.get("REQ_ALLOWED_DIR", os.path.join(HERE, "..")))

server = MCPServer("requirements-checker-v2")


def safe_path(csv_path: str) -> str:
    """Return a checked absolute path. ToolError sends a clear message back to Claude."""
    if not csv_path:
        return rules.SAMPLE_CSV
    path = os.path.realpath(os.path.expanduser(csv_path))
    if os.path.commonpath([path, ALLOWED_DIR]) != ALLOWED_DIR:
        log.warning("Blocked read outside allowed folder: %s", path)
        raise ToolError(f"{csv_path} is outside the allowed folder {ALLOWED_DIR}")
    if not path.endswith(".csv"):
        raise ToolError("Only .csv files can be read")
    return path


# ---------------------------------------------------------------- tools (v1, now guarded)
@server.tool(description="List every requirement in a CSV file (columns: id,text). "
                         "Leave csv_path empty to use the built-in synthetic sample.")
def list_requirements(csv_path: str = "") -> list[dict]:
    return rules.list_requirements(safe_path(csv_path))


@server.tool(description="Run rule-based quality checks on one requirement: weak modal verbs, vague wording, "
                         "TBD/TBC, more than one 'shall', and no measurable value. Returns a verdict and issues.")
def check_requirement(req_id: str, csv_path: str = "") -> dict:
    return rules.check_requirement(req_id, safe_path(csv_path))


# ---------------------------------------------------------------- 1. progress notifications
@server.tool(description="Check every requirement in a CSV and return a summary plus the ones that need review. "
                         "Sends progress updates while it runs.")
async def check_all(ctx: Context, csv_path: str = "") -> dict:
    path = safe_path(csv_path)
    reqs = rules.list_requirements(path)
    log.info("check_all: %d requirements from %s", len(reqs), path)

    results = []
    for i, req in enumerate(reqs, start=1):
        results.append(rules.check_requirement(req["id"], path))
        await ctx.report_progress(i, len(reqs), f"{i}/{len(reqs)} checked")

    failing = [r for r in results if r.get("issues")]
    return {
        "checked": len(results),
        "passed": len(results) - len(failing),
        "needs_review": len(failing),
        "failing": failing,
    }


# ---------------------------------------------------------------- 2. elicitation
class MissingValue(BaseModel):
    """The form the user sees. Elicitation only allows flat, simple fields."""
    value: float = Field(description="The number the requirement should state, e.g. 30")
    unit: str = Field(description="Its unit, e.g. seconds, hours, Hz, %")
    condition: str = Field(default="", description="Optional: when it applies, e.g. 'from power-on'")


@server.tool(description="Help fix one requirement. If it has no measurable value, this asks the USER for the "
                         "number and unit, then returns everything needed to rewrite it. Use the user's value "
                         "exactly; never invent a number.")
async def fix_requirement(req_id: str, ctx: Context, csv_path: str = "") -> dict:
    result = rules.check_requirement(req_id, safe_path(csv_path))
    if "error" in result:
        return result

    needs_number = any("measurable" in issue.lower() or "tbd" in issue.lower() for issue in result["issues"])
    if not needs_number:
        return {**result, "user_value": None,
                "instruction": "No number needed. Rewrite using 'shall' and fix the listed issues."}

    answer = await ctx.elicit(
        message=f"{req_id}: \"{result['text']}\"\nThis has no measurable value. What should it be?",
        schema=MissingValue,
    )
    if answer.action != "accept":
        log.info("fix_requirement: user %sd the value for %s", answer.action, req_id)
        return {**result, "user_value": None,
                "instruction": "The user gave no value. Rewrite it, mark any number as [assumed] and say so."}

    v = answer.data
    log.info("fix_requirement: %s = %s %s", req_id, v.value, v.unit)
    return {**result,
            "user_value": {"value": v.value, "unit": v.unit, "condition": v.condition},
            "instruction": "Rewrite as one 'shall' statement using exactly this value, unit and condition."}


# ---------------------------------------------------------------- resources and prompt
@server.resource("requirements://sample", name="sample-requirements",
                 description="Synthetic requirements for a flight data logger", mime_type="text/csv")
def sample_requirements() -> str:
    with open(rules.SAMPLE_CSV) as f:
        return f.read()


@server.resource("requirements://sample/{req_id}", name="sample-requirement",
                 description="One requirement from the sample, by id (e.g. REQ-002)", mime_type="text/plain")
def sample_requirement(req_id: str) -> str:
    return rules.load_requirements().get(req_id, f"No requirement with id {req_id}")


@server.prompt(description="Review every requirement, then fix the failing ones with real values from the user")
def review_requirements() -> str:
    return ("Use check_all on the sample requirements and give a one-line summary. "
            "Then call fix_requirement for each one that needs review, and write the testable rewrite "
            "it asks for. Only use numbers the user supplied; mark anything else as [assumed].")


if __name__ == "__main__":
    log.info("Allowed folder: %s", ALLOWED_DIR)
    if "--http" in sys.argv:
        # Stateless: every request stands alone, so it can scale or restart freely.
        server.run("streamable-http", host="127.0.0.1", port=8000, stateless_http=True, json_response=True)
    else:
        server.run()
