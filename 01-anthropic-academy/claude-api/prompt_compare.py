"""Compare two system prompts with the same eval: v1 (original) vs v2 (prompt-engineered).

Anthropic Academy, Building with the Claude API, section 3 (Prompt engineering techniques).
Uses the dataset and graders from eval.py, so the only thing that changes is the prompt.

Run:  python3 prompt_compare.py
"""
import json

from eval import DATASET, MAX_WORDS, PASS_SCORE, MODEL, SYSTEM, ask, code_grade, model_grade

V1 = SYSTEM

# v2 applies techniques from the module:
#   1. Be clear and direct: say exactly who the audience is
#   2. Hard, specific constraint: a word limit with headroom below the 120 the eval checks
#   3. Structure with XML tags so the rules are unambiguous
#   4. Show, don't tell: one example of the answer shape we want
V2 = """You are a friendly coding mentor for complete beginners.

<rules>
- Answer in 80 words or fewer. This is a hard limit: count your words before replying.
- Start with a one-sentence, plain-English definition.
- Then give one short, concrete example.
- No headings, no bullet lists, and no code longer than 3 lines.
</rules>

<example>
Question: What is a variable?
Answer: A variable is a named box that stores a value so your program can use it later. For example, age = 30 stores 30 in a box called age, and print(age) shows it. You can change what's in the box at any time.
</example>"""


def run(system, case):
    answer = ask(case["question"], system)
    checks = code_grade(answer, case["keywords"])
    grade = model_grade(case["question"], answer)
    passed = checks["short_enough"] and checks["has_keyword"] and grade["score"] >= PASS_SCORE
    return {"answer": answer, **checks, **grade, "passed": passed}


def cell(r):
    mark = "PASS" if r["passed"] else "FAIL"
    return f"{mark} {r['words']:>3}w {r['score']:>2}/10"


def summary(results):
    n = len(results)
    return (sum(r["passed"] for r in results), n,
            sum(r["score"] for r in results) / n,
            sum(r["words"] for r in results) / n)


def main():
    print(f"Prompt v1 vs v2 on {MODEL}: {len(DATASET)} questions, limit {MAX_WORDS} words\n")
    print(f"{'Question':<40} {'v1':<18} {'v2':<18}")
    print("-" * 76)
    v1_results, v2_results = [], []
    for i, case in enumerate(DATASET, 1):
        r1, r2 = run(V1, case), run(V2, case)
        v1_results.append({**case, **r1})
        v2_results.append({**case, **r2})
        q = f"{i}. {case['question']}"[:39]
        print(f"{q:<40} {cell(r1):<18} {cell(r2):<18}")

    p1, n, s1, w1 = summary(v1_results)
    p2, _, s2, w2 = summary(v2_results)
    print("-" * 76)
    print(f"{'Passed':<40} {f'{p1}/{n}':<18} {f'{p2}/{n}':<18}")
    print(f"{'Average score':<40} {f'{s1:.1f}/10':<18} {f'{s2:.1f}/10':<18}")
    print(f"{'Average words':<40} {f'{w1:.0f}':<18} {f'{w2:.0f}':<18}")

    with open("compare_results.json", "w") as f:
        json.dump({"v1": {"prompt": V1, "results": v1_results},
                   "v2": {"prompt": V2, "results": v2_results}}, f, indent=2)
    print("\nFull answers saved to compare_results.json")


if __name__ == "__main__":
    main()
