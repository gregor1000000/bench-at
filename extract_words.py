import csv
import re
import sys
from pathlib import Path

from pdfminer.high_level import extract_text


def extract_questions(text: str) -> list[dict]:
    lines = text.split("\n")

    qnum_pattern = re.compile(r"^(\d+)\.\s*(.*)")
    ans_pattern = re.compile(r"^([A-E])\.\s+(.+)")

    raw_questions: list[dict] = []
    answer_blocks: list[list[dict]] = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = qnum_pattern.match(line)
        if m:
            qnum = m.group(1)
            letters = m.group(2).strip()
            if not letters:
                i += 1
                while i < len(lines) and not lines[i].strip():
                    i += 1
                letters = lines[i].strip() if i < len(lines) else ""

            letters = letters.strip()
            if letters and not re.match(r"^[A-E]\.", letters) and not letters.startswith("Seite"):
                raw_questions.append({"question_id": qnum, "letters": letters})
        else:
            am = ans_pattern.match(line)
            if am:
                ans_set = []
                while i < len(lines) and am:
                    key = am.group(1)
                    val = am.group(2).strip()
                    if val.startswith("Keine"):
                        val = ""
                    ans_set.append({"key": key, "value": val})
                    if len(ans_set) == 5:
                        break
                    i += 1
                    while i < len(lines) and not lines[i].strip():
                        i += 1
                    if i < len(lines):
                        am = ans_pattern.match(lines[i].strip())
                    else:
                        am = None
                if len(ans_set) == 5:
                    answer_blocks.append(ans_set)
                continue
        i += 1

    # Match questions to answer blocks in pairs (odd/even column layout)
    questions = []
    nq = len(raw_questions)
    for idx in range(0, nq, 2):
        q_odd = raw_questions[idx]
        if idx + 1 < nq:
            q_even = raw_questions[idx + 1]
        else:
            q_even = None

        block_idx = idx // 2
        if block_idx * 2 + 1 < len(answer_blocks):
            odd_block = answer_blocks[block_idx * 2]
            even_block = answer_blocks[block_idx * 2 + 1]
        elif block_idx < len(answer_blocks):
            odd_block = answer_blocks[block_idx]
            even_block = None
        else:
            odd_block = None
            even_block = None

        if odd_block:
            q_odd.update({f"{a['key']}_ans": a["value"] for a in odd_block})
        if even_block and q_even:
            q_even.update({f"{a['key']}_ans": a["value"] for a in even_block})

    # If last odd question had no even partner, still include it
    for q in raw_questions:
        if q not in questions:
            questions.append(q)

    return questions


def main():
    pdf_path = Path(__file__).parent / "Wortflüssigkeit.pdf"
    csv_path = Path(__file__).parent / "Wortflüssigkeit.csv"

    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting text from {pdf_path}...")
    text = extract_text(str(pdf_path))

    print("Parsing questions...")
    questions = extract_questions(text)

    header = [
        "question_id",
        "letters",
        "A_ans", "B_ans", "C_ans", "D_ans", "E_ans",
    ]

    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for q in questions:
            row = [
                q.get("question_id", ""),
                q.get("letters", ""),
                q.get("A_ans", ""),
                q.get("B_ans", ""),
                q.get("C_ans", ""),
                q.get("D_ans", ""),
                q.get("E_ans", ""),
            ]
            w.writerow(row)

    print(f"Done — {len(questions)} questions written to {csv_path}")


if __name__ == "__main__":
    main()
