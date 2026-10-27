"""Scripted MCP client that tests v2: progress, elicitation (auto-answers 30 seconds), folder guard, resource template."""
import asyncio, json, sys
from mcp import types
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

SERVER = __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "requirements_server_v2.py")

async def on_elicit(ctx, params):
    print("  ELICIT:", params.message.replace("\n", " | "))
    return types.ElicitResult(action="accept", content={"value": 30, "unit": "seconds", "condition": "from power-on"})

async def on_progress(progress, total, message):
    print(f"  progress {progress}/{total} {message}")

def show(r):
    print(" ", (r.structured_content or r.content[0].text) if not r.is_error else ("ERROR " + r.content[0].text))

async def main():
    params = StdioServerParameters(command=sys.executable, args=[SERVER])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w, elicitation_callback=on_elicit) as s:
            await s.initialize()
            print("tools:", [t.name for t in (await s.list_tools()).tools])
            print("templates:", [t.uri_template for t in (await s.list_resource_templates()).resource_templates])
            print("check_all:"); res = await s.call_tool("check_all", {}, progress_callback=on_progress)
            sc = res.structured_content or json.loads(res.content[0].text); print("  summary", sc["checked"], sc["passed"], sc["needs_review"])
            print("fix REQ-002:"); show(await s.call_tool("fix_requirement", {"req_id": "REQ-002"}))
            print("fix REQ-008:"); show(await s.call_tool("fix_requirement", {"req_id": "REQ-008"}))
            print("guard:"); show(await s.call_tool("list_requirements", {"csv_path": "/etc/passwd.csv"}))
            print("resource:", (await s.read_resource("requirements://sample/REQ-005")).contents[0].text)
asyncio.run(main())
