"""Reflection-based requirement rewriter (Agentic AI, Module 2: the reflection design pattern).

For every requirement that fails the rule checks:

  1. DRAFT     Claude rewrites it into testable 'shall' requirement(s).
  2. FEEDBACK  My Python rule checker runs on the draft (external, objective feedback).
  3. REFLECT   Claude critiques its own draft against that feedback and a checklist, then revises.
  4. Repeat 2-3 until the rules pass and the critique finds nothing to fix (max 3 rounds).

Then it compares the first draft (no reflection) with the final version, so you can see
whether reflection actually helped, measured by the same rules, not by vibes.

Run:  python3 reflection_rewriter.py                      (sample requirements)
      python3 reflection_rewriter.py my_reqs.csv --rounds 2
All requirements are synthetic. Don't feed it real programme data.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "01-anthropic-academy", "shared"))
import requirements_rules as rules  # noqa: E402

MODEL = "claude-sonnet-5-5"

DRAFT_PROMPT = """You are a systems engineer rewriting one requirement so it can be verified.
Rules: use 'shall', one 'shall' per requirement (split compound ones), give a number and a unit,
keep the original intent, no vague words (fast, user-friendly, adequate, appropriate, typical...).
Where you must invent a value, put [assumed] right after it.

Original ({req_id}): {text}

Reply with JSON only: {{"rewrites": ["..."], "verification": ["test|analysis|inspection|demonstration", ...]}}
(one verification method per rewrite)."""

REFLECT_PROMPT = """You wrote this rewrite of a requirement. Review it like a requirements reviewer, then improve it.

Original ({req_id}): {text}
Your draft: {draft}

External rule-checker results on your draft (objective, from code):
{feedback}

Checklist: (1) every rule issue fixed; (2) original intent kept, nothing added that the original
didn't ask for; (3) every invented value tagged [assumed]; (4) one 'shall' each, with a number
and unit; (5) the verification method fits.

Reply with JSON only:
{{"critique": "one or two sentences on what's wrong, or 'No changes needed.'",
  "rewrites": ["..."], "verification": ["...", ...]}}"""


def ask(client, prompt, retries=1):
    """One Claude call that must return JSON. Reads text blocks only (skips thinking blocks).
    If the reply is cut off or isn't valid JSON, asks once more for a shorter, JSON-only reply."""
    messages = [{"role": "user", "content": prompt}]
    for attempt in range(retries + 1):
        resp = client.messages.create(model=MODEL, max_tokens=4000, messages=messages)
        raw = "".join(b.text for b in resp.content if b.type == "text").strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)  # tolerate ```json fences
        try:
            if getattr(resp, "stop_reason", None) == "max_tokens":
                raise ValueError("reply was cut off at max_tokens")
            return json.loads(raw)
        except ValueError as e:  # JSONDecodeError is a ValueError
            if attempt == retries:
                raise
            messages = [{"role": "user", "content": prompt},
                        {"role": "assistant", "content": raw or "(empty)"},
                        {"role": "user", "content": f"That reply wasn't usable ({e}). Reply again with valid "
                                                    "JSON only, nothing else, and keep the critique to two sentences."}]


def check_all(rewrites):
    """External feedback: run my rule checker on every rewrite."""
    return [rules.check_text(r) for r in rewrites]


def all_pass(results):
    return all(r["verdict"] == "PASS" for r in results)


def improve(client, req, max_rounds):
    draft = ask(client, DRAFT_PROMPT.format(req_id=req["id"], text=req["text"]))
    first = {"rewrites": draft["rewrites"], "checks": check_all(draft["rewrites"])}
    history = [{"round": 0, "critique": "(first draft)", **first}]
    current = first
    for rnd in range(1, max_rounds + 1):
        feedback = json.dumps([{"text": c["text"], "verdict": c["verdict"], "issues": c["issues"]}
                               for c in current["checks"]], indent=1)
        out = ask(client, REFLECT_PROMPT.format(req_id=req["id"], text=req["text"],
                                                draft=json.dumps(current["rewrites"]), feedback=feedback))
        current = {"rewrites": out["rewrites"], "checks": check_all(out["rewrites"])}
        history.append({"round": rnd, "critique": out["critique"], **current})
        if all_pass(current["checks"]) and out["critique"].strip().lower().startswith("no changes"):
            break  # rules pass and the reviewer is satisfied: stop reflecting
    return {"id": req["id"], "original": req["text"], "first": first, "final": current,
            "rounds": history[-1]["round"], "history": history}


def report(results):
    lines = ["# Reflection run", "",
             "| Req | First draft passes rules | After reflection passes rules | Reflection rounds |",
             "| --- | --- | --- | --- |"]
    for r in results:
        f = sum(c["verdict"] == "PASS" for c in r["first"]["checks"])
        g = sum(c["verdict"] == "PASS" for c in r["final"]["checks"])
        lines.append(f"| {r['id']} | {f}/{len(r['first']['checks'])} | {g}/{len(r['final']['checks'])} | {r['rounds']} |")
    first_ok = sum(all_pass(r["first"]["checks"]) for r in results)
    final_ok = sum(all_pass(r["final"]["checks"]) for r in results)
    lines += ["", f"**Fully passing: {first_ok}/{len(results)} without reflection, "
                  f"{final_ok}/{len(results)} with reflection.**", ""]
    for r in results:
        lines += [f"## {r['id']}", f"Original: {r['original']}", ""]
        for h in r["history"]:
            lines.append(f"- Round {h['round']}: {h['critique']}")
            for c in h["checks"]:
                lines.append(f"    - [{c['verdict']}] {c['text']}" + (f" ({'; '.join(c['issues'])})" if c["issues"] else ""))
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?", default=rules.SAMPLE_CSV)
    ap.add_argument("--rounds", type=int, default=3, help="max reflection rounds per requirement")
    args = ap.parse_args()

    import anthropic
    from dotenv import load_dotenv
    load_dotenv(override=True)
    os.environ["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY", "").strip().strip("\"'“”‘’")
    client = anthropic.Anthropic()

    to_fix = [r for r in rules.list_requirements(args.csv)
              if rules.check_requirement(r["id"], args.csv)["verdict"] == "REVIEW"]
    print(f"{len(to_fix)} requirements need work. Reflecting (max {args.rounds} rounds each)...\n")
    results = []
    for req in to_fix:
        try:
            res = improve(client, req, args.rounds)
        except Exception as e:  # one bad reply shouldn't lose the whole run
            print(f"{req['id']}: skipped ({type(e).__name__}: {e})")
            continue
        print(f"{req['id']}: {res['rounds']} round(s) -> "
              f"{'PASS' if all_pass(res['final']['checks']) else 'still REVIEW'}")
        results.append(res)

    md = report(results)
    out = os.path.join(HERE, "reflection_output.md")
    with open(out, "w") as f:
        f.write(md + "\n")
    print("\n" + md.split("\n## ")[0])
    print(f"Full log: {out}")


if __name__ == "__main__":
    main()
