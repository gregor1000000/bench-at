import csv

from data.extract import RAW_DIR, fingerprint, write_tasks

SOURCE = RAW_DIR / "Wortflüssigkeit.csv"


def extract() -> list[dict]:
    tasks = []
    with open(SOURCE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            options = {}
            for letter in "ABCDE":
                val = row.get(f"{letter}_ans", "")
                options[letter] = val

            data = {
                "type": "words",
                "slot": row["question_id"],
                "letters": row["letters"],
                "options": options,
            }
            data["fingerprint"] = fingerprint(data)
            tasks.append(data)
    return tasks


def main():
    print("Extracting words...")
    tasks = extract()
    write_tasks("words", tasks)


if __name__ == "__main__":
    main()
