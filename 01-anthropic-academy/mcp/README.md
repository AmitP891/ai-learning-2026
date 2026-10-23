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
