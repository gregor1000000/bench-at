import os
import sys
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def load_env():
    if not ENV_PATH.exists():
        print("Error: .env file not found at", ENV_PATH, file=sys.stderr)
        sys.exit(1)
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip()


def call_llm(messages: list[dict], model: str = "google/gemma-4-26b-a4b-it", timeout: int = 120) -> str:
    api_key = os.environ.get("OPEN_ROUTER_API_KEY")
    if not api_key:
        print("Error: OPEN_ROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "messages": messages},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        print(f"API error: {e}", file=sys.stderr)
        if hasattr(e, "response") and e.response is not None:
            print(e.response.text[:2000], file=sys.stderr)
        sys.exit(1)
