from bench_at.prompts.numbers import build_prompt as build_numbers
from bench_at.prompts.words import build_prompt as build_words
from bench_at.prompts.figures import build_messages as build_figures
from bench_at.registry import Registry


def build_messages(task_type: str, task: dict, registry: Registry) -> list[dict]:
    if task_type == "numbers":
        prompt = build_numbers(task)
        return [{"role": "user", "content": prompt}]
    elif task_type == "words":
        prompt = build_words(task)
        return [{"role": "user", "content": prompt}]
    elif task_type == "figures":
        return build_figures(task, registry)
    else:
        raise ValueError(f"Unknown task type: {task_type}")


def build_prompt(task_type: str, task: dict) -> str:
    if task_type == "numbers":
        return build_numbers(task)
    elif task_type == "words":
        return build_words(task)
    else:
        raise ValueError(f"Task type {task_type} has no text prompt")
