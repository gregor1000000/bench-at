import base64
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import requests
from pypdf import PdfReader, PdfWriter
from pdfminer.high_level import extract_text


BASE_DIR = Path(__file__).parent
PDF_PATH = BASE_DIR / "3000 Figuren Medium.pdf"
ENV_PATH = BASE_DIR / ".env"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-3.1-pro-preview"
PROBLEMS_PER_PAGE = 3


def load_env():
    if not ENV_PATH.exists():
        print("Error: .env file not found", file=sys.stderr)
        sys.exit(1)
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip()


def build_problem_index() -> dict[int, int]:
    """Returns {problem_id: page_number_0idx} for all problems."""
    reader = PdfReader(str(PDF_PATH))
    total_pages = len(reader.pages)
    index = {}
    for page_idx in range(total_pages):
        for offset in range(PROBLEMS_PER_PAGE):
            prob_id = page_idx * PROBLEMS_PER_PAGE + offset + 1
            if prob_id > 3000:
                break
            index[prob_id] = page_idx
    return index


def list_problems(page_num: int) -> list[int]:
    start = (page_num - 1) * PROBLEMS_PER_PAGE + 1
    return list(range(start, start + PROBLEMS_PER_PAGE))


def page_to_png(page_num: int, dpi: int = 200) -> bytes:
    reader = PdfReader(str(PDF_PATH))
    writer = PdfWriter()
    writer.add_page(reader.pages[page_num])

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        tmp_pdf_path = tmp_pdf.name
        writer.write(tmp_pdf_path)

    tmp_png_path = tmp_pdf_path.replace(".pdf", ".png")
    try:
        subprocess.run(
            ["sips", "-s", "format", "png", "--resampleWidth", str(dpi * 4),
             tmp_pdf_path, "--out", tmp_png_path],
            capture_output=True, check=True,
        )
        with open(tmp_png_path, "rb") as f:
            return f.read()
    finally:
        for p in [tmp_pdf_path, tmp_png_path]:
            try:
                os.unlink(p)
            except OSError:
                pass


def parse_problem_selection(raw: str, prob_index: dict) -> list[int]:
    ids = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, _, b = part.partition("-")
            for i in range(int(a.strip()), int(b.strip()) + 1):
                ids.add(i)
        elif part.isdigit():
            ids.add(int(part))
    valid = sorted(i for i in ids if i in prob_index)
    if not valid:
        print("No valid problem IDs in selection.", file=sys.stderr)
        sys.exit(1)
    return valid


def build_messages(selected_problems: list[int], prob_index: dict) -> list[dict]:
    system_msg = {
        "role": "system",
        "content": (
            "You are solving a geometric reasoning test."
            "Each page shows several problems (numbered 1., 2., 3.). Each problem "
            "presents a sliced-up geometric form on the left and five assembled "
            "options (A-E) on the right. Your task: determine which option correctly "
            "assembles the pieces. Explain your reasoning for each problem."
        ),
    }

    pages_needed = sorted(set(prob_index[p] for p in selected_problems))
    selected_set = set(selected_problems)

    user_content = []
    for page_idx in pages_needed:
        probs_on_page = [p for p in range(
            page_idx * PROBLEMS_PER_PAGE + 1,
            page_idx * PROBLEMS_PER_PAGE + PROBLEMS_PER_PAGE + 1
        ) if p in prob_index]

        focus = [p for p in probs_on_page if p in selected_set]
        others = [p for p in probs_on_page if p not in selected_set]

        label = f"Page {page_idx + 1}"
        if focus:
            label += f" — solve problems {', '.join(str(p) for p in focus)}"
        if others:
            label += f" (ignore problems {', '.join(str(p) for p in others)})"

        img_bytes = page_to_png(page_idx)
        b64 = base64.b64encode(img_bytes).decode()

        user_content.append({"type": "text", "text": f"\n--- {label} ---"})
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"},
        })

    return [system_msg, {"role": "user", "content": user_content}]


def call_llm(messages: list[dict]) -> str:
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
            json={"model": MODEL, "messages": messages},
            timeout=300,
        )
        if not resp.ok:
            print(f"HTTP {resp.status_code}:", file=sys.stderr)
            print(resp.text[:2000], file=sys.stderr)
            sys.exit(1)
        return resp.json()["choices"][0]["message"]["content"]
    except (requests.RequestException, ValueError) as e:
        print(f"API error: {e}", file=sys.stderr)
        try:
            print("Raw response:", resp.text[:2000], file=sys.stderr)
        except NameError:
            pass
        sys.exit(1)


def main():
    dryrun = "--dryrun" in sys.argv

    load_env()

    if not PDF_PATH.exists():
        print(f"Error: {PDF_PATH} not found", file=sys.stderr)
        sys.exit(1)

    prob_index = build_problem_index()
    total = len(prob_index)
    print(f"{total} problems in PDF (1-{total}).")

    selection_raw = input("Select problems (e.g. 1,3,5-10,42): ").strip()

    if selection_raw.lower() == "list":
        for pid in sorted(prob_index):
            page = prob_index[pid] + 1
            print(f"  Problem {pid:>4} → page {page}")
        selection_raw = input("Select problems: ").strip()

    selected = parse_problem_selection(selection_raw, prob_index)

    if dryrun:
        import json, copy
        pages_needed = sorted(set(prob_index[p] for p in selected))
        print(f"Selected {len(selected)} problem(s), spanning {len(pages_needed)} page(s)\n")
        preview_dir = BASE_DIR / ".preview"
        preview_dir.mkdir(exist_ok=True)
        saved_pages = set()
        for p in selected:
            page_idx = prob_index[p]
            if page_idx in saved_pages:
                continue
            saved_pages.add(page_idx)
            img_bytes = page_to_png(page_idx)
            probs_on = sorted(pi for pi in selected if prob_index[pi] == page_idx)
            img_path = preview_dir / f"page{page_idx + 1}_problems_{'_'.join(str(x) for x in probs_on)}.png"
            img_path.write_bytes(img_bytes)
            print(f"  Preview: {img_path}")

        messages = build_messages(selected, prob_index)
        truncated = copy.deepcopy(messages)
        for msg in truncated:
            if isinstance(msg.get("content"), list):
                for item in msg["content"]:
                    if item.get("type") == "image_url":
                        url = item["image_url"]["url"]
                        b64 = url.split("base64,", 1)[-1]
                        size = len(b64)
                        item["image_url"]["url"] = f"data:image/png;base64,{b64[:40]}...({size} total chars)"
        print(json.dumps(truncated, indent=2))
        return

    print(f"\nSelected {len(selected)} problem(s). Sending to {MODEL}...\n")
    messages = build_messages(selected, prob_index)
    response = call_llm(messages)
    print(response)


if __name__ == "__main__":
    main()
