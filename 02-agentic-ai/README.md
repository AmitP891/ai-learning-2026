# Agentic AI (DeepLearning.AI, Andrew Ng)

| Module | Topic | Status |
| --- | --- | --- |
| 1 | Introduction to agentic workflows | Done 29 Oct 2026 (quiz is paid-only, skipped) |
| 2 | Reflection design pattern | Next |
| 3 | Tool use | |
| 4 | Practical tips for building agentic AI | |
| 5 | Planning and multi-agent workflows | |

## Module 1 exercise: my builds on the autonomy spectrum

Module 1's point: "agentic" isn't yes or no. Systems sit on a spectrum, from **less autonomous** (my code fixes the steps; the model fills each one in) to **highly autonomous** (the model plans its own steps, picks or writes its tools, and checks its own work).

The four design patterns from lesson 8 are **reflection**, **tool use**, **planning** and **multi-agent collaboration**.

| Build | Reflection | Tool use | Planning | Multi-agent | Autonomy |
| --- | --- | --- | --- | --- | --- |
| [Requirements checker script](../01-anthropic-academy/claude-api/requirements_checker.py) (week 2) | – | ✅ Claude decides when to call `list_requirements` / `check_requirement` | – (my loop) | – | **Low to medium** |
| [Prompt eval](../01-anthropic-academy/claude-api/eval.py) (week 2) | Partly: Claude grades answers, code checks the grader | – | – | Partly: writer model + grader model | **Low** |
| [MCP server v1](../01-anthropic-academy/mcp/requirements_server.py) | – | ✅ Claude Code picks tools and order | Light: it orders its own review | – | **Medium** |
| [MCP server v2](../01-anthropic-academy/mcp/requirements_server_v2.py) | – | ✅ plus progress and elicitation | Light | Human in the loop: the server asks me for real values | **Medium, deliberately capped** |
| [Bit: Level 1](../brand/motion/bit-level-1/BRIEF.md) | ✅ critique loop: scored 6 criteria, fixed, re-rendered (3 → 8) | ✅ installed its own toolchain, wrote and ran code | ✅ beat grid, gates, its own build order | – (one agent, plus me at the gates) | **High, with gates** |

### What I take from it
1. **More autonomy isn't automatically better.** Bit: Level 1 could be highly autonomous because a mistake costs a 10-second re-render. Requirements on a real project are different, so MCP v2 deliberately stops and asks me instead of guessing.
2. **Gates are how you allow autonomy safely.** The Bit run planned and fixed things on its own, but couldn't move past a gate without my approval. That's the same idea as design reviews.
3. **Reflection needs a measurable target.** "Make it better" doesn't converge; "score 6 criteria, stop at 8/10" did, in 2 rounds.
4. **Gap:** none of my builds use multi-agent collaboration yet. That's Module 5, and it's the planned "writer agent vs reviewer agent" build.
