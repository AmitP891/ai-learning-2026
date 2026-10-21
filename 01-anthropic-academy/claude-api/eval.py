"""Prompt evaluation for chat.py's system prompt.

Anthropic Academy, Building with the Claude API, section 2 (Prompt evaluation).
Runs a small test set through the prompt, then grades every answer two ways:
  1. Code graders: fast, exact checks (length limit, required keywords)
  2. Model grader: a second Claude call scores the answer 1-10 with a reason
"""
import json
import re

import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

MODEL = "claude-sonnet-5-5"   # the model being tested
GRADER = "claude-haiku-5-5"   # a cheaper, faster model does the marking
SYSTEM = "You are a concise, friendly coding mentor. Keep answers under 120 words."
MAX_WORDS = 120
PASS_SCORE = 7

# Each case: a question, plus words a good answer should mention (any one is enough)
DATASET = [
    {"question": "What is an API?", "keywords": ["interface", "request", "programs"]},
    {"question": "What does git commit do?", "keywords": ["snapshot", "save", "history"]},
    {"question": "Explain a Python list in one sentence.", "keywords": ["ordered", "collection", "items"]},
    {"question": "Why should I never commit an API key?", "keywords": ["secret", "access", "public"]},
    {"question": "What is JSON?", "keywords": ["text", "format", "data"]},
    {"question": "What does a for loop do?", "keywords": ["repeat", "each", "iterate"]},
]


def text_of(response):
    """Newer models can return 'thinking' blocks first, so read text blocks by type."""
    return "".join(b.text for b in response.content if b.type == "text").strip()


def ask(question, system=SYSTEM):
    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    return text_of(response)


def code_grade(answer, keywords):
    words = len(answer.split())
    short_enough = words <= MAX_WORDS
    has_keyword = any(k in answer.lower() for k in keywords)
    return {"words": words, "short_enough": short_enough, "has_keyword": has_keyword}


def model_grade(question, answer):
    prompt = f"""You are grading an answer from a coding mentor for beginners.

Question: {question}
Answer: {answer}

Score 1-10 for accuracy and clarity for a beginner.
Reply with only JSON, like: {{"score": 8, "reason": "one short sentence"}}"""
    response = client.messages.create(
        model=GRADER,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    match = re.search(r"\{.*\}", text_of(response), re.DOTALL)
    if not match:
        return {"score": 0, "reason": "grader did not return JSON"}
    return json.loads(match.group())


def main():
    print(f"Evaluating {MODEL} on {len(DATASET)} test cases\n")
    results = []
    for i, case in enumerate(DATASET, 1):
        answer = ask(case["question"])
        checks = code_grade(answer, case["keywords"])
        grade = model_grade(case["question"], answer)
        passed = checks["short_enough"] and checks["has_keyword"] and grade["score"] >= PASS_SCORE
        results.append({**case, "answer": answer, **checks, **grade, "passed": passed})

        mark = "PASS" if passed else "FAIL"
        print(f"[{mark}] {i}. {case['question']}")
        print(f"       {checks['words']} words | keyword: {'yes' if checks['has_keyword'] else 'no'}"
              f" | score: {grade['score']}/10 | {grade['reason']}\n")

    passed = sum(r["passed"] for r in results)
    average = sum(r["score"] for r in results) / len(results)
    print(f"Result: {passed}/{len(results)} passed | average score {average:.1f}/10")

    with open("eval_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Full answers saved to eval_results.json")


if __name__ == "__main__":
    main()
