import hashlib
import json
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw"
CANONICAL_DIR = BASE_DIR / "canonical"


def fingerprint(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()[:12]


def canonical_path(task_type: str) -> Path:
    p = CANONICAL_DIR / task_type
    p.mkdir(parents=True, exist_ok=True)
    return p / "tasks.jsonl"


def write_tasks(task_type: str, tasks: list[dict]) -> None:
    path = canonical_path(task_type)
    with open(path, "w") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"  wrote {len(tasks)} tasks to {path}")
