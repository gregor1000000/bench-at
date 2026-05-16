import argparse
import sys
from pathlib import Path

from bench_at.llm import call_llm, load_env
from bench_at.registry import Registry
from bench_at.runner import run_tasks

BASE_DIR = Path(__file__).parent
DEFAULT_MODEL = "google/gemma-4-26b-a4b-it"
DEFAULT_FIGURES_MODEL = "google/gemini-3.1-pro-preview"

REGISTRY = Registry()


def cmd_process():
    from data.extract.process_all import main as process_main
    process_main()


def _select_interactive(task_type: str) -> list[dict]:
    tasks = REGISTRY.by_type(task_type)
    print(f"{len(tasks)} problems loaded.")

    raw = input("\nSelect problems by ID (e.g. 1,3,5-10,42, or 'list'): ").strip()

    if raw.lower() == "list":
        for t in tasks:
            if task_type == "numbers":
                seq = ", ".join(str(n) for n in t["sequence"])
                print(f"  {t['slot']:>4}: {seq}")
            elif task_type == "words":
                print(f"  {t['slot']:>4}: {t['letters']}")
            elif task_type == "figures":
                print(f"  {t['slot']:>4}: {t['image']}")
        raw = input("\nSelect problems by ID: ").strip()

    ids = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            for i in range(int(a.strip()), int(b.strip()) + 1):
                ids.add(str(i))
        elif part.isdigit():
            ids.add(part)

    selected = [t for t in tasks if t["slot"] in ids]
    if not selected:
        print(f"No tasks matched: {raw}", file=sys.stderr)
        sys.exit(1)
    return selected


def cmd_interactive(task_type: str, dryrun: bool):
    model = DEFAULT_FIGURES_MODEL if task_type == "figures" else DEFAULT_MODEL
    selected = _select_interactive(task_type)

    if dryrun:
        from bench_at.prompts import build_messages, build_prompt
        for t in selected:
            print(f"\n--- {task_type}/{t['slot']} ---")
            if task_type == "figures":
                msgs = build_messages(task_type, t, REGISTRY)
                print(f"[{msgs[0]['role']}] {msgs[0]['content'][:100]}...")
                content = msgs[1]["content"]
                n_parts = len(content)
                has_img = any(c.get("type") == "image_url" for c in content)
                print(f"[{msgs[1]['role']}] <{n_parts} parts, image={has_img}>")
            else:
                print(build_prompt(task_type, t))
        return

    from bench_at.prompts import build_messages
    print(f"\nSelected {len(selected)} problem(s). Sending to {model}...\n")
    for t in selected:
        msgs = build_messages(task_type, t, REGISTRY)
        response = call_llm(msgs, model=model, timeout=300 if task_type == "figures" else 120)
        print(response)
        print("\n" + "=" * 50 + "\n")


def cmd_run(args):
    model = args.model or (DEFAULT_FIGURES_MODEL if args.type == "figures" else DEFAULT_MODEL)
    output = args.output or str(BASE_DIR / "evaluation" / f"{args.type}_{model.split('/')[-1]}.jsonl")

    Path(output).parent.mkdir(parents=True, exist_ok=True)

    tasks = REGISTRY.by_type(args.type)

    if args.range:
        parts = args.range.split("-", 1)
        start, end = int(parts[0]), int(parts[1]) if len(parts) > 1 else int(parts[0])
        tasks = [t for t in tasks if start <= int(t["slot"]) <= end]

    if not tasks:
        print("No tasks match the criteria.", file=sys.stderr)
        sys.exit(1)

    print(f"Running {len(tasks)} {args.type} tasks with {model} -> {output}")
    run_tasks(tasks, model=model, output_path=output, registry=REGISTRY, dryrun=args.dryrun)


def main():
    load_env()
    REGISTRY.load()

    parser = argparse.ArgumentParser(description="BENCH-AT Benchmark Runner")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("process", help="Re-extract canonical tasks from raw files")

    for name in ("numbers", "words", "figures"):
        p = sub.add_parser(name, help=f"Solve {name} problems interactively")
        p.add_argument("--dryrun", action="store_true", help="Preview without calling API")

    run_parser = sub.add_parser("run", help="Run tasks in batch")
    run_parser.add_argument("type", choices=["numbers", "words", "figures"])
    run_parser.add_argument("--model", help="Model identifier (default: per-type)")
    run_parser.add_argument("--output", help="Output JSONL path")
    run_parser.add_argument("--range", help="e.g. 1-50 or 42")
    run_parser.add_argument("--dryrun", action="store_true", help="Preview without calling API")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "process":
        cmd_process()
    elif args.command == "run":
        cmd_run(args)
    else:
        cmd_interactive(args.command, args.dryrun)


if __name__ == "__main__":
    main()
