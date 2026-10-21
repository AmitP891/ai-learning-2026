# Claude API: multi-turn chat

My first script from **Building with the Claude API**, section 1 (Accessing Claude with the API).

## What it shows

- Calling the Messages API with the official Python SDK
- **Multi-turn conversations**: the API is stateless, so the script keeps a `messages` list and sends the full history every turn
- **Content blocks**: Claude Sonnet 5.5 thinks by default, so a response can start with a `thinking` block. The script reads blocks by `type` instead of assuming `content[0]` is text
- **System prompts**: setting Claude's role and style once, separate from the conversation
- **Temperature (a lesson learned)**: the course covers it, but newer models such as Claude Sonnet 5.5 no longer accept custom `temperature`, `top_p` or `top_k` values, so this script leaves them out. See the [Sonnet 5.5 migration guide](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide).

## Run it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key-here"   # from console.anthropic.com, never commit it
python chat.py
```

Type `quit` to exit.

## Next

The tool-use section extends this same loop so Claude can call Python functions.

---

# Prompt evaluation: `eval.py`

From section 2 (Prompt evaluation). Instead of eyeballing answers, `eval.py` tests the chat's system prompt against a fixed set of questions and scores every answer.

## How it grades

| Grader | What it checks | Why |
| --- | --- | --- |
| Code | Answer is under 120 words | The system prompt promises this, so test it |
| Code | Answer mentions at least one expected keyword | A cheap check that it's on topic |
| Model | A second Claude call (Haiku) scores accuracy and clarity 1–10 with a reason | Catches quality issues code can't |

A case passes only if all three pass (score of 7 or more). The script prints a pass/fail line per question, an overall score, and saves every answer to `eval_results.json`.

## Run it

```bash
python3 eval.py
```

It makes 12 API calls (6 answers + 6 grades), so it takes a minute or so.

## Try this

Change the `SYSTEM` prompt, run the eval again, and compare the scores. That's the point of evals: you can measure whether a prompt change made things better or worse.

---

# Prompt engineering: `prompt_compare.py`

From section 3 (Prompt engineering techniques). The eval found one failure in the original prompt: a 9/10 answer that broke the 120-word limit. This script fixes the prompt and proves it, by running the **same 6 questions and the same graders** against two prompts:

| | v1 (original) | v2 (engineered) |
| --- | --- | --- |
| Audience | "coding mentor" | "mentor for complete beginners" |
| Length | "under 120 words" | "80 words or fewer, a hard limit: count before replying" (headroom below the check) |
| Structure | One sentence | Rules in `<rules>` XML tags |
| Shape | Not specified | Definition, then one example; plus a worked `<example>` |

It prints a side-by-side table (PASS/FAIL, words and score per question) and totals for each prompt, and saves both sets of answers to `compare_results.json`.

```bash
python3 prompt_compare.py
```

24 API calls (6 questions × 2 prompts × answer + grade), so allow a couple of minutes.
