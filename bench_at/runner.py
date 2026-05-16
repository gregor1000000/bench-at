import json
import time
from datetime import datetime, timezone

from bench_at.llm import call_llm
from bench_at.prompts import build_messages
from bench_at.registry import Registry


def run_tasks(
    tasks: list[dict],
    model: str,
    output_path: str,
    registry: Registry,
    *,
    dryrun: bool = False,
):
    total = len(tasks)
    results = []

    if dryrun:
        for task in tasks:
            msgs = build_messages(task["type"], task, registry)
            print(f"\n--- {task['type']}/{task['slot']} ---")
            for m in msgs:
                role = m["role"]
                content = m["content"]
                if isinstance(content, str):
                    print(f"[{role}] {content[:200]}...")
                else:
                    print(f"[{role}] <multimodal: {len(content)} parts>")
        return

    for i, task in enumerate(tasks, 1):
        fingerprint = task["fingerprint"]
        print(f"[{i}/{total}] {task['type']}/{task['slot']} ({fingerprint}) ... ", end="", flush=True)

        messages = build_messages(task["type"], task, registry)
        timeout = 300 if task["type"] == "figures" else 120

        start = time.time()
        try:
            response = call_llm(messages, model=model, timeout=timeout)
            elapsed = time.time() - start
            print(f"{elapsed:.1f}s")
        except Exception as e:
            response = f"ERROR: {e}"
            print(f"FAILED: {e}")

        record = {
            "type": task["type"],
            "slot": task["slot"],
            "fingerprint": fingerprint,
            "model": model,
            "response": response,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        results.append(record)

        with open(output_path, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    successes = sum(1 for r in results if not r["response"].startswith("ERROR"))
    print(f"\nDone: {successes}/{total} succeeded, results in {output_path}")
