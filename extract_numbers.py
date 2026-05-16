import csv
import re
import sys
from pathlib import Path

from pdfminer.high_level import extract_text


def extract_questions(text: str) -> list[dict]:
    questions = []
    lines = text.split("\n")
    i = 0

    qnum_pattern = re.compile(r"^(\d+)\.\s*(.*)")

    while i < len(lines):
        line = lines[i].strip()
        m = qnum_pattern.match(line)
        if not m:
            i += 1
            continue

        qnum = m.group(1)
        rest = m.group(2).strip()

        if not rest:
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            seq_line = lines[i].strip() if i < len(lines) else ""
        else:
            seq_line = rest

        seq_nums = re.findall(r"\d+", seq_line)
        while len(seq_nums) < 9:
            seq_nums.append("")

        answers = {}
        for _ in range(5):
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i >= len(lines):
                break
            ans_line = lines[i].strip()
            am = re.match(r"([A-E])\.\s*(.+)", ans_line)
            if am:
                key = am.group(1)
                val = am.group(2).strip()
                if "Keine Antwort" in val:
                    answers[key] = ["", ""]
                else:
                    parts = re.findall(r"\d+", val)
                    answers[key] = [parts[0], parts[1]] if len(parts) >= 2 else ["", ""]

        row = {"question_id": qnum}
        for j, num in enumerate(seq_nums[:7], 1):
            row[f"n{j}"] = num
        row["unk1"] = "?"
        row["unk2"] = "?"
        for letter in ["A", "B", "C", "D", "E"]:
            a1, a2 = answers.get(letter, ["", ""])
            row[f"{letter}_ans1"] = a1
            row[f"{letter}_ans2"] = a2

        questions.append(row)
        i += 1

    return questions


def main():
    pdf_path = Path(__file__).parent / "Zahlenfolgen.pdf"
    csv_path = Path(__file__).parent / "Zahlenfolgen.csv"

    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting text from {pdf_path}...")
    text = extract_text(str(pdf_path))

    print("Parsing questions...")
    questions = extract_questions(text)

    header = [
        "question_id",
        "n1", "n2", "n3", "n4", "n5", "n6", "n7",
        "unk1", "unk2",
        "A_ans1", "A_ans2", "B_ans1", "B_ans2",
        "C_ans1", "C_ans2", "D_ans1", "D_ans2",
        "E_ans1", "E_ans2",
    ]

    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for q in questions:
            w.writerow([q.get(h, "") for h in header])

    print(f"Done — {len(questions)} questions written to {csv_path}")


if __name__ == "__main__":
    main()
