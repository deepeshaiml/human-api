"""Render every PDF page and produce contact sheets for visual QA."""
from __future__ import annotations

from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables"
RENDER_ROOT = OUT / "rendered_pages"
PDF_NAMES = [
    "HumanAPI_Business_Review.pdf",
    "HumanAPI_Pitch_Deck.pdf",
    "HumanAPI_Idea_Document.pdf",
    "HumanAPI_Business_Case.pdf",
    "HumanAPI_Competitive_Analysis.pdf",
    "HumanAPI_Evaluation_Report.pdf",
]


def main() -> None:
    for name in PDF_NAMES:
        source = OUT / name
        pdf = pdfium.PdfDocument(source)
        folder = RENDER_ROOT / source.stem
        folder.mkdir(parents=True, exist_ok=True)
        pages: list[Image.Image] = []
        empty_pages: list[int] = []
        for index in range(len(pdf)):
            page = pdf[index]
            text = page.get_textpage().get_text_range().strip()
            if not text:
                empty_pages.append(index + 1)
            image = page.render(scale=1.5).to_pil().convert("RGB")
            image.save(folder / f"page-{index + 1:02d}.png", optimize=True)
            pages.append(image)
        cols = 3 if "Pitch_Deck" in name else (2 if len(pages) > 1 else 1)
        thumb_w = 540 if cols == 3 else 640
        gap, label_h = 18, 32
        thumbs = []
        for i, page in enumerate(pages):
            ratio = thumb_w / page.width
            thumb = page.resize((thumb_w, int(page.height * ratio)), Image.Resampling.LANCZOS)
            thumb = ImageOps.expand(thumb, border=1, fill="#cbd5e1")
            canvas = Image.new("RGB", (thumb.width, thumb.height + label_h), "white")
            canvas.paste(thumb, (0, label_h))
            ImageDraw.Draw(canvas).text((8, 8), f"Page {i + 1}", fill="#334155")
            thumbs.append(canvas)
        rows = (len(thumbs) + cols - 1) // cols
        cell_w = max(im.width for im in thumbs)
        cell_h = max(im.height for im in thumbs)
        sheet = Image.new("RGB", (cols * cell_w + (cols + 1) * gap,
                                  rows * cell_h + (rows + 1) * gap), "#e2e8f0")
        for i, thumb in enumerate(thumbs):
            x = gap + (i % cols) * cell_w
            y = gap + (i // cols) * cell_h
            sheet.paste(thumb, (x, y))
        sheet.save(OUT / f"{source.stem}_Contact_Sheet.png", optimize=True)
        print(f"{name}: {len(pages)} pages rendered; empty text pages={empty_pages}")


if __name__ == "__main__":
    main()
