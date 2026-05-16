import csv
import os
import re
import sys
import requests
from pathlib import Path


BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "Wortflüssigkeit.csv"
ENV_PATH = BASE_DIR / ".env"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemma-4-26b-a4b-it"


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
    lines.append("Below are word fluency problems (Wortflüssigkeit) from a German test.")
    lines.append("Each problem gives a set of scrambled letters that form a German word.")
    lines.append("Your task: find the German word formed by these letters, then select")
    lines.append("the answer option (A-E) that shows the FIRST LETTER of that word.")
    lines.append("If none of the letters A-D match, the answer is E (Keine Antwort ist richtig).")
    lines.append("Explain your reasoning for each problem.\n")
    lines.append("---\n")
    for q in selected:
        letters = q["letters"]
        ans_parts = []
        for l in "ABCDE":
            a = q.get(f"{l}_ans", "")
            ans_parts.append(f"  {l}: {a if a else '(Keine Antwort)'}")
        lines.append(f"Problem {q['question_id']}: Letters = {letters}")
        lines.append("Options:")
        lines.append("\n".join(ans_parts))
        lines.append("")
    lines.append("---\n")
    lines.append("For each problem, tell me:")
    lines.append("Which answer option is correct and what German word do the letters form?")
    return "\n".join(lines)


def call_llm(prompt: str) -> str:
    api_key = os.environ.get("OPEN_ROUTER_API_KEY")
    if not api_key:
        print("Error: OPEN_ROUTER_API_KEY not set in environment or .env", file=sys.stderr)
        sys.exit(1)

    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": MODEL, "messages": [{"role": "user", "content": prompt}]},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except (requests.RequestException, ValueError) as e:
        print(f"API error: {e}", file=sys.stderr)
        try:
            print("Raw response:", resp.text[:2000], file=sys.stderr)
        except NameError:
            pass
        sys.exit(1)


def main():
    dryrun = "--dryrun" in sys.argv

    load_env()
    questions = read_questions()

    if not questions:
        print("No questions found in CSV.", file=sys.stderr)
        sys.exit(1)

    print(f"{len(questions)} problems loaded. Enter IDs or 'list' to see them.")
    selection_raw = input("\nSelect problems by ID (e.g. 1,3,5-10,42): ").strip()

    if selection_raw.lower() == "list":
        for q in questions:
            print(f"  {q['question_id']:>4}: {q['letters']}")
        selection_raw = input("\nSelect problems by ID: ").strip()

    selected = parse_selection(questions, selection_raw)
    prompt = build_prompt(selected)

    if dryrun:
        print(prompt)
        return

    print(f"\nSelected {len(selected)} problem(s). Sending to {MODEL}...\n")
    response = call_llm(prompt)
    print(response)


if __name__ == "__main__":
    main()
