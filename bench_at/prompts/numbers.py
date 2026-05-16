INSTRUCTIONS = """\
Below are number sequence problems from a test called Number Sequences.
Each problem shows a sequence of 7 numbers (n1..n7) where the last two are marked '?'.
For each problem, 5 answer options (A through E) are given, each with two numbers (ans1, ans2).
Your task: determine the correct answer(s) and explain the pattern/rule behind the sequence.
Explain your reasoning step by step for each problem.
---"""

FOOTER = """\
---
For each problem above, tell me:
Which answer option(s) are correct and why?"""


def build_prompt(task: dict) -> str:
    seq = ", ".join(str(n) for n in task["sequence"])
    ans_parts = []
    for letter in "ABCDE":
        vals = task["options"].get(letter, [])
        if vals:
            ans_parts.append(f"  {letter}: ({vals[0]}, {vals[1]})")
        else:
            ans_parts.append(f"  {letter}: (Keine Antwort)")

    problem = (
        f"Problem {task['slot']}: Sequence = [{seq}]\n"
        f"Options:\n" + "\n".join(ans_parts)
    )
    return INSTRUCTIONS + "\n\n" + problem + "\n\n" + FOOTER
