# Agentic AI (DeepLearning.AI, Andrew Ng)

| Module | Topic | Status |
| --- | --- | --- |
| 1 | Introduction to agentic workflows | Done 29 Oct 2026 (quiz is paid-only, skipped) |
| 2 | Reflection design pattern | Done (6 Nov 2026) |
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

## Module 2 exercise: reflection on my requirements rewriter

**Reflection** = the model produces a draft, then critiques its own output and revises it. It works best with **external feedback**: something outside the model that checks the draft objectively (code, a test, a tool), instead of the model only marking its own homework.

My version, [`reflection_rewriter.py`](reflection_rewriter.py):

1. **Draft:** Claude rewrites each failing requirement into testable `shall` statements.
2. **Feedback:** my Python rule checker (`requirements_rules.check_text`) checks the draft: weak modals, vague words, TBDs, compound shalls, no number + unit.
3. **Reflect:** Claude gets the rule results plus a reviewer checklist (intent kept, `[assumed]` on invented values, verification method fits) and revises.
4. **Stop** when the rules pass and the critique says "No changes needed", or after 3 rounds.

It compares the **first draft** (no reflection) with the **final** version using the same rules, so the benefit is measured, not assumed. Results are written to `reflection_output.md`.

```bash
cd 02-agentic-ai
python3 reflection_rewriter.py              # sample requirements, max 3 rounds
python3 reflection_rewriter.py --rounds 1   # one reflection round only
```

### Results from the first real run (6 Nov 2026)

Full log: [`reflection_output.md`](reflection_output.md). Six vague requirements, up to 3 reflection rounds each.

| Question | Answer |
| --- | --- |
| Passed the rules without vs with reflection? | **6/6 vs 6/6.** Every first draft already passed my rule checker, so by that metric reflection added nothing. |
| Rounds needed? | **3 for all six.** The critic never said "No changes needed", so the stopping rule never fired. |
| Did reflection make anything worse? | **Once.** REQ-005 round 2 shortened the battery requirement and reintroduced the vague word "typical". The rule checker flagged it and round 3 fixed it. |
| Did the critique find things my rules miss? | **Yes, lots.** Invented scope (non-volatile memory, a data server, extra Bluetooth features, legibility and contrast nobody asked for), untagged assumptions (AES, Bluetooth Low Energy), and fuzzy measurement points ("respond" became "send the last byte", "95 percent" became "at least 95 percent"). |

### What I learned
1. **Measure with the right metric.** My rules check *form* (shall, numbers, vague words). Reflection improved *intent* (no invented scope, honest assumptions). A form-only eval scored both versions 6/6, so it couldn't see the improvement. That's lesson 17: an eval has to measure what you're trying to improve.
2. **External feedback and self-critique catch different things.** The code caught a regression the model introduced ("typical"); the model caught over-reach the code can't see. Use both.
3. **Reflection needs a stopping rule that can actually stop.** An LLM critic always finds something. Next version: stop when the rules pass and the critique raises nothing new since the last round, or cap at 2 rounds (most of the value arrived in round 1).
4. **Cost:** 4 API calls per requirement instead of 1, so reflection is worth it for important outputs, not everything.

### Next version (ideas)
- Add an intent check to the eval: count `[assumed]` tags and flag any new noun phrase not in the original (invented scope).
- Stop after 2 rounds or when the critique repeats itself.

### Notes from the lessons
- (add as I go)
