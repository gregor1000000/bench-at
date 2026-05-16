import json
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
CANONICAL_DIR = BASE_DIR / "data" / "canonical"


class Registry:
    """Loads tasks from canonical JSONL files and provides lookup."""

    def __init__(self):
        self._tasks: list[dict] = []
        self._by_type: dict[str, list[dict]] = {}
        self._by_fingerprint: dict[str, dict] = {}
        self._by_slot: dict[str, dict] = {}

    def load(self) -> None:
        for task_type in ["numbers", "words", "figures"]:
            path = CANONICAL_DIR / task_type / "tasks.jsonl"
            if not path.exists():
                continue
            with open(path) as f:
                for line in f:
                    t = json.loads(line)
                    self._tasks.append(t)
                    self._by_type.setdefault(task_type, []).append(t)
                    self._by_fingerprint[t["fingerprint"]] = t
                    key = f"{task_type}/{t['slot']}"
                    self._by_slot[key] = t
        self._tasks.sort(key=lambda t: (t["type"], int(t["slot"])))

    @property
    def tasks(self) -> list[dict]:
        return self._tasks

    def by_type(self, task_type: str) -> list[dict]:
        return self._by_type.get(task_type, [])

    def by_fingerprint(self, fp: str) -> Optional[dict]:
        return self._by_fingerprint.get(fp)

    def by_slot(self, task_type: str, slot: str) -> Optional[dict]:
        return self._by_slot.get(f"{task_type}/{slot}")

    def resolve(self, ref: str) -> Optional[dict]:
        """Resolve 'numbers/001' or a bare fingerprint."""
        if "/" in ref:
            parts = ref.split("/", 1)
            return self.by_slot(parts[0], parts[1])
        return self.by_fingerprint(ref)

    def count(self) -> int:
        return len(self._tasks)

    def __repr__(self) -> str:
        return (
            f"Registry({self.count()} tasks: "
            + ", ".join(f"{k}={len(v)}" for k, v in self._by_type.items())
            + ")"
        )
