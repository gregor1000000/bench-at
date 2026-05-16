import csv
import os
import json
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path


BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "Zahlenfolgen.csv"
ENV_PATH = BASE_DIR / ".env"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def load_env():
    if not ENV_PATH.exists():
        print("Error: .env file not found", file=sys.stderr)
        sys.exit(1)
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip()


def read_questions() -> list[dict]:
    with open(CSV_PATH, newline="") as f:
        return list(csv.DictReader(f))


def display_questions(questions: list[dict]):
    print(f"\n{'='*80}")
    print(f"{'ID':>4} | {'Sequence (n1..n7)':>40} | {'Answers (A..E)':>30}")
    print(f"{'='*80}")
    for q in questions:
        seq = ", ".join(q[f"n{i}"] for i in range(1, 8))
        ans_keys = [f"{l}_ans1" for l in "ABCDE"]
        ans_str = " / ".join(
            f"{l}:{q[k]},{q[k.replace('_ans1','_ans2')]}"
            for l, k in zip("ABCDE", ans_keys)
        )
        print(f"{q['question_id']:>4} | {seq:>40} | {ans_str[:60]}")


def parse_selection(questions: list[dict], raw: str) -> list[dict]:
    ids = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\d+)\s*-\s*(\d+)$", part)
        if m:
            for i in range(int(m.group(1)), int(m.group(2)) + 1):
                ids.add(str(i))
        elif part.isdigit():
            ids.add(part)
    selected = [q for q in questions if q["question_id"] in ids]
    if not selected:
        print(f"No questions matched selection: {raw}", file=sys.stderr)
        sys.exit(1)
    return selected


def build_prompt(selected: list[dict]) -> str:
    lines = []
    lines.append("Below are number sequence problems from a test called Number Sequences'.")
    lines.append("Each problem shows a sequence of 7 numbers (n1..n7) where the last two are marked '?'.")
    lines.append("For each problem, 5 answer options (A through E) are given, each with two numbers (ans1, ans2).")
    lines.append("Your task: determine the correct answer(s) and explain the pattern/rule behind the sequence.")
    lines.append("Explain your reasoning step by step for each problem.\n")
    lines.append("---")
    lines.append("")
    for q in selected:
        seq = ", ".join(q[f"n{i}"] for i in range(1, 8))
        lines.append(f"Problem {q['question_id']}: Sequence = [{seq}]")
        ans_parts = []
        for l in "ABCDE":
            a1 = q.get(f"{l}_ans1", "")
            a2 = q.get(f"{l}_ans2", "")
            ans_parts.append(f"  {l}: ({a1}, {a2})")
        lines.append("Options:")
        lines.append("\n".join(ans_parts))
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("For each problem above, tell me:")
    lines.append("1. What is the pattern/rule of the sequence?")
    lines.append("2. Which answer option(s) are correct and why?")
    return "\n".join(lines)


def call_llm(prompt: str) -> str:
    api_key = os.environ.get("OPEN_ROUTER_API_KEY")
    if not api_key:
        print("Error: OPEN_ROUTER_API_KEY not set in environment or .env", file=sys.stderr)
        sys.exit(1)

    payload = json.dumps({
        "model": "deepseek/deepseek-v4-flash:free",
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/opencode-ai",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    load_env()
    questions = read_questions()

    if not questions:
        print("No questions found in CSV.", file=sys.stderr)
        sys.exit(1)

    display_questions(questions)

    print(f"\nTotal: {len(questions)} problems")
    selection_raw = input("\nSelect problems by ID (e.g. 1,3,5-10,42): ").strip()
    selected = parse_selection(questions, selection_raw)

    print(f"\nSelected {len(selected)} problem(s). Building prompt and sending to LLM...\n")
    prompt = build_prompt(selected)

    response = call_llm(prompt)
    print(response)


if __name__ == "__main__":
    main()
