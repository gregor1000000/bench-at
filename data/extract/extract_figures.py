import io
import os
import subprocess
import tempfile

from PIL import Image
from pypdf import PdfReader, PdfWriter

from data.extract import RAW_DIR, CANONICAL_DIR, fingerprint, write_tasks

PDF_PATH = RAW_DIR / "3000 Figuren Medium.pdf"
PROBLEMS_DIR = CANONICAL_DIR / "figures" / "problems"
DPI = 200
PROBLEMS_PER_PAGE = 3


def render_page(page_idx: int) -> Image.Image:
    reader = PdfReader(str(PDF_PATH))
    writer = PdfWriter()
    writer.add_page(reader.pages[page_idx])

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmppdf = tmp.name
        writer.write(tmppdf)

    tmp_png = tmppdf + ".png"
    try:
        subprocess.run(
            ["sips", "-s", "format", "png", "--resampleWidth", str(DPI * 4),
             tmppdf, "--out", tmp_png],
            capture_output=True, check=True,
        )
        return Image.open(tmp_png).copy()
    finally:
        for p in [tmppdf, tmp_png]:
            try:
                os.unlink(p)
            except OSError:
                pass


def crop_problem(page_img: Image.Image, offset: int) -> bytes:
    w, h = page_img.size
    crop_h = h // PROBLEMS_PER_PAGE
    cropped = page_img.crop((0, offset * crop_h, w, (offset + 1) * crop_h))
    buf = io.BytesIO()
    cropped.save(buf, format="PNG")
    return buf.getvalue()


def extract() -> list[dict]:
    reader = PdfReader(str(PDF_PATH))
    total_pages = len(reader.pages)
    total_problems = total_pages * PROBLEMS_PER_PAGE

    tasks = []
    for page_idx in range(total_pages):
        page_img = render_page(page_idx)
        for offset in range(PROBLEMS_PER_PAGE):
            slot = page_idx * PROBLEMS_PER_PAGE + offset + 1
            if slot > total_problems:
                break

            png_bytes = crop_problem(page_img, offset)
            png_path = PROBLEMS_DIR / f"{slot:04d}.png"
            png_path.write_bytes(png_bytes)

            data = {
                "type": "figures",
                "slot": str(slot),
                "image": f"problems/{slot:04d}.png",
            }
            data["fingerprint"] = fingerprint(data)
            tasks.append(data)

    return tasks


def main():
    print("Extracting figures...")
    PROBLEMS_DIR.mkdir(parents=True, exist_ok=True)
    tasks = extract()
    write_tasks("figures", tasks)


if __name__ == "__main__":
    main()
