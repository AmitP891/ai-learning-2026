# Requirements checker: MCP server

Week 3 milestone. The two tools from [`requirements_checker.py`](../claude-api/requirements_checker.py) are packaged as an **MCP server**, so any MCP client can use them. That means Claude Code and Claude Desktop, not just my own script.

| Type | Name | What it does |
| --- | --- | --- |
| Tool | `list_requirements(csv_path?)` | Lists every requirement in a CSV (`id,text`) |
| Tool | `check_requirement(req_id, csv_path?)` | Rule checks: weak modal, vague wording, TBD, compound, not measurable |
| Resource | `requirements://sample` | The synthetic flight-logger requirements |
| Prompt | `review_requirements` | A ready-made "review everything and rewrite" request |

The rules live in [`../shared/requirements_rules.py`](../shared/requirements_rules.py), shared with the tool-use script, so both always check the same things.

No API key is needed. The client's Claude does the reasoning; this server only runs the checks.

## Install

```bash
pip3 install -r requirements.txt      # MCP Python SDK v2
```

## Use it in Claude Code

```bash
claude mcp add requirements-checker -- python3 ~/ai-learning-2026/01-anthropic-academy/mcp/requirements_server.py
```

Then start `claude` and ask: *"Use requirements-checker to review the sample requirements."*

## Use it in Claude Desktop

Add this to `~/Library/Application Support/Claude/claude_desktop_config.json`, then restart Claude Desktop:

```json
{
  "mcpServers": {
    "requirements-checker": {
      "command": "python3",
      "args": ["/Users/amitpatel/ai-learning-2026/01-anthropic-academy/mcp/requirements_server.py"]
    }
  }
}
```

Synthetic or public requirements only.

## v2 (MCP Advanced Topics)

[`requirements_server_v2.py`](requirements_server_v2.py) adds:

| Feature | MCP concept | What it does |
| --- | --- | --- |
| `check_all(csv_path?)` | Progress notifications | Checks the whole CSV and reports "4/8 checked" as it goes |
| `fix_requirement(req_id, csv_path?)` | Elicitation | Pauses and asks **you** for the missing number and unit, so the rewrite uses a real value, not an invented one. Clients without form support (e.g. the Claude desktop app) get told to ask in chat instead |
| `requirements://sample/{req_id}` | Resource template | Read one requirement by id |
| Folder guard | (replaces roots) | Only reads `.csv` files inside `REQ_ALLOWED_DIR` (default: this course folder) |
| `--http` | Streamable HTTP, stateless | Serves at `http://127.0.0.1:8000/mcp` as well as stdio |

The MCP spec of 2026-07-28 deprecated sampling, roots and protocol logging ([SEP-2577](https://modelcontextprotocol.io/seps/2577-deprecate-roots-sampling-and-logging)), so v2 uses elicitation, a configured folder and stderr logging instead.

```bash
claude mcp add requirements-checker-v2 -- python3 ~/ai-learning-2026/01-anthropic-academy/mcp/requirements_server_v2.py
python3 test_server_v2.py      # scripted test, no Claude needed
```
