import csv

from data.extract import RAW_DIR, fingerprint, write_tasks

SOURCE = RAW_DIR / "Zahlenfolgen.csv"
KEYS = ["n1", "n2", "n3", "n4", "n5", "n6", "n7"]


def extract() -> list[dict]:
    tasks = []
    with open(SOURCE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sequence = [int(row[k]) for k in KEYS]
            options = {}
            for letter in "ABCDE":
                a1 = row.get(f"{letter}_ans1", "")
                a2 = row.get(f"{letter}_ans2", "")
                if a1 and a2:
                    options[letter] = [int(a1), int(a2)]
                else:
                    options[letter] = []

            data = {
                "type": "numbers",
                "slot": row["question_id"],
                "sequence": sequence,
                "options": options,
            }
            data["fingerprint"] = fingerprint(data)
            tasks.append(data)
    return tasks


def main():
    print("Extracting numbers...")
    tasks = extract()
    write_tasks("numbers", tasks)


if __name__ == "__main__":
    main()
