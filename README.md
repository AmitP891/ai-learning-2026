# AI Learning 2026

A 12-week AI learning sprint (Oct 2026 – Jan 2027): agentic AI, MCP, and AI for systems engineering. Every milestone ships code here, and every course produces public content.

Follow along: [vibewithamit.com](https://vibewithamit.com) · TikTok [@vibewithamitai](https://www.tiktok.com/@vibewithamitai) · YouTube [@vibewithamitai](https://www.youtube.com/@vibewithamitai) · Instagram [@vibewithamitai](https://www.instagram.com/vibewithamitai/), with videos, posts and write-ups from each week.

## Progress

| Week | Course | Milestone | Status |
| --- | --- | --- | --- |
| 1 | Anthropic Academy | Claude Code in Action certificate | ✅ Done |
| 2 | Anthropic Academy | API tool-use script | ✅ Done |
| 3 | Anthropic Academy | Custom MCP server | ✅ Done |
| 4–8 | Agentic AI (Andrew Ng) | Reflection, tool use, evals, multi-agent | ⬜ |
| 8 | PPI AI for Systems Engineering | Workshop attended | ⬜ |
| 9–11 | Hugging Face AI Agents Course | Agent rebuilt in LangGraph, certificate | ⬜ |
| 12 | Capstone | Requirements traceability agent demo | ⬜ |

## Structure

```
01-anthropic-academy/     Claude Code, Claude API, MCP projects
02-agentic-ai/            Agent design patterns and evals (DeepLearning.AI)
03-huggingface-agents/    smolagents and LangGraph work
04-capstone/              Requirements traceability agent (synthetic data only)
content/                  Links to videos, posts and blog articles
website/                  Vibe with Amit site (vibewithamit.com), deployed to Netlify
```

## Highlights

- **MCP server (Week 3):** the requirements checker's tools packaged as an MCP server and connected to Claude Code, which called them 9 times in one review, then pointed out gaps in the rules themselves. [Code](01-anthropic-academy/mcp/)
- **Requirements checker (Week 2):** Claude used two Python tools to review 8 synthetic system requirements, flagged 6 (vague wording, weak modal verbs, a TBD, a compound requirement) and rewrote each as testable, marking invented values as [assumed]. [Code](01-anthropic-academy/claude-api/requirements_checker.py) · [sample output](01-anthropic-academy/claude-api/sample_output.md)
- **Prompt v1 vs v2 (Week 2):** four prompt engineering techniques took the eval from 5/6 to 6/6 across two runs, with answers 39% shorter and quality up from 8.7 to 8.8. [Code](01-anthropic-academy/claude-api/prompt_compare.py)
- **Eval caught the AI grader (Week 2):** a 9/10 answer broke the 120-word limit; a one-line code check caught it. [Code](01-anthropic-academy/claude-api/eval.py)

## Certificates

- [Claude Code in Action](01-anthropic-academy/certificates/claude-code-in-action.pdf) — Anthropic, Oct 2026
- [Introduction to Model Context Protocol](01-anthropic-academy/certificates/introduction-to-mcp.pdf) — Anthropic, Oct 2026
- [Model Context Protocol: Advanced Topics](01-anthropic-academy/certificates/mcp-advanced-topics.pdf) — Anthropic, Oct 2026

## Note

All examples use synthetic or public data only.
