INSTRUCTIONS = """\
Below are word fluency problems (Wortflüssigkeit) from a German test.
Each problem gives a set of scrambled letters that form a German word.
Your task: find the German word formed by these letters, then select
the answer option (A-E) that shows the FIRST LETTER of that word.
If none of the letters A-D match, the answer is E (Keine Antwort ist richtig).
Explain your reasoning for each problem.
---"""

FOOTER = """\
---
For each problem, tell me:
Which answer option is correct and what German word do the letters form?"""


def build_prompt(task: dict) -> str:
    ans_parts = []
    for letter in "ABCDE":
        val = task["options"].get(letter, "")
        ans_parts.append(f"  {letter}: {val if val else '(Keine Antwort)'}")

    problem = (
        f"Problem {task['slot']}: Letters = {task['letters']}\n"
        f"Options:\n" + "\n".join(ans_parts)
    )
    return INSTRUCTIONS + "\n\n" + problem + "\n\n" + FOOTER
