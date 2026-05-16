import base64

from bench_at.registry import CANONICAL_DIR

SYSTEM_PROMPT = (
    "You are solving a geometric reasoning test."
    " Each problem presents a sliced-up geometric form and five assembled "
    "options (A-E). Your task: determine which option correctly "
    "assembles the pieces. Explain your reasoning for each problem."
)


def build_messages(task: dict) -> list[dict]:
    img_path = CANONICAL_DIR / "figures" / task["image"]
    b64 = base64.b64encode(img_path.read_bytes()).decode()

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"Problem {task['slot']}"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ],
        },
    ]
