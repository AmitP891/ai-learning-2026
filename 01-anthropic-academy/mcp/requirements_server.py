"""Requirements checker as an MCP server.

Anthropic Academy, Introduction to MCP. The same two tools as requirements_checker.py,
packaged with the Model Context Protocol so any MCP client (Claude Code, Claude Desktop)
can use them. No API key needed: the client's Claude does the thinking, this server
only runs the checks.

Exposes:
  tools      list_requirements, check_requirement
  resource   requirements://sample      (the sample CSV)
  prompt     review_requirements        (a ready-made review request)

Run directly to test:  python3 requirements_server.py   (it waits on stdin; Ctrl+C to stop)
"""
import os
import sys

from mcp.server.mcpserver import MCPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shared"))
import requirements_rules as rules  # noqa: E402

server = MCPServer("requirements-checker")


@server.tool(description="List every requirement in a CSV file (columns: id,text). "
                         "Leave csv_path empty to use the built-in synthetic sample.")
def list_requirements(csv_path: str = "") -> list[dict]:
    return rules.list_requirements(csv_path or rules.SAMPLE_CSV)


@server.tool(description="Run rule-based quality checks on one requirement: weak modal verbs, vague wording, "
                         "TBD/TBC, more than one 'shall', and no measurable value. Returns a verdict and issues.")
def check_requirement(req_id: str, csv_path: str = "") -> dict:
    return rules.check_requirement(req_id, csv_path or rules.SAMPLE_CSV)


@server.resource("requirements://sample", name="sample-requirements",
                 description="Synthetic requirements for a flight data logger", mime_type="text/csv")
def sample_requirements() -> str:
    with open(rules.SAMPLE_CSV) as f:
        return f.read()


@server.prompt(description="Review every requirement and suggest testable rewrites")
def review_requirements() -> str:
    return ("Use the requirements-checker tools to list every requirement and check each one. "
            "Then give a one-line summary, and for each requirement that needs review: the main issue "
            "and a rewritten, testable version using 'shall' and a measurable value. "
            "Mark any number you invent as [assumed].")


if __name__ == "__main__":
    server.run()
