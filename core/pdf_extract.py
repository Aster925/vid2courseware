# -*- coding: utf-8 -*-
"""
Extract existing PDF courseware into Markdown text + images.

For text-based PDFs (a text layer present), pulls the text directly — no OCR
needed. Embedded images above a size threshold are saved alongside (e.g. the
picture-based questions in a reading/listening test). Scanned PDFs would need
OCR instead — run inspect() first to see which kind you have.

把已有 PDF 提取成「Markdown 文本 + 图片」。文字版直接抽文字层；图片题的内嵌图按页导出。

Usage:
    python -m core.pdf_extract --pdf-dir "path/to/pdfs"
    python -m core.pdf_extract --inspect           # just report each PDF's nature
"""
import os
import re
import sys
import json
import argparse

sys.stdout.reconfigure(encoding="utf-8")
from core.cfg import load_config
import fitz  # PyMuPDF


def clean(t):
    t = t.replace("’", "'").replace("‘", "'")
    t = re.sub(r"\s+'\s*|\s*'\s+", "'", t)   # "d' age" → "d'age"
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--pdf-dir")
    ap.add_argument("--inspect", action="store_true", help="report nature only, don't extract")
    ap.add_argument("--min-image-bytes", type=int, default=3072)
    args = ap.parse_args()

    cfg = load_config(args.config)
    pdf_dir = args.pdf_dir or cfg.get("pdf_dir") or ""
    out_dir = cfg.get("output_dir", "./output")
    if not pdf_dir or not os.path.isdir(pdf_dir):
        sys.exit("Set pdf_dir in config.yaml or pass --pdf-dir")

    dst = os.path.join(out_dir, "pdf_extract")
    os.makedirs(dst, exist_ok=True)
    summary = []

    for fn in sorted(os.listdir(pdf_dir)):
        if not fn.lower().endswith(".pdf") or fn.startswith("._"):
            continue
        path = os.path.join(pdf_dir, fn)
        stem = os.path.splitext(fn)[0].strip()
        try:
            doc = fitz.open(path)
        except Exception as e:
            print(f"[err] {fn}: {e}")
            continue
        npages = doc.page_count
        chars = sum(len(p.get_text("text").strip()) for p in doc)
        imgs_total = sum(len(p.get_images(full=True)) for p in doc)
        kind = "text" if chars > npages * 200 else ("scanned/image" if imgs_total >= npages else "sparse")

        if args.inspect:
            summary.append({"file": fn, "pages": npages, "chars": chars, "images": imgs_total, "kind": kind})
            print(f"  {stem:<30} {npages:>3}p {chars:>7}c {imgs_total:>3}img  {kind}")
            doc.close()
            continue

        md = [f"# {stem}\n", f"> from `{fn}` — {npages} pages, kind: {kind}\n"]
        img_dir = os.path.join(dst, stem + "_imgs")
        n_img, seen = 0, set()
        for i, pg in enumerate(doc, 1):
            txt = clean(pg.get_text("text"))
            if txt:
                md.append(f"\n## p.{i}\n\n{txt}\n")
            for img in pg.get_images(full=True):
                xref = img[0]
                if xref in seen:
                    continue
                seen.add(xref)
                try:
                    ext = doc.extract_image(xref)
                    if len(ext["image"]) < args.min_image_bytes:
                        continue
                    os.makedirs(img_dir, exist_ok=True)
                    rel = f"{stem}_imgs/p{i:02d}_x{xref}.{ext['ext']}"
                    with open(os.path.join(dst, rel), "wb") as f:
                        f.write(ext["image"])
                    n_img += 1
                    md.append(f"\n![p{i}]({rel})\n")
                except Exception:
                    pass
        with open(os.path.join(dst, stem + ".md"), "w", encoding="utf-8") as f:
            f.write("\n".join(md))
        summary.append({"file": fn, "pages": npages, "kind": kind, "images_kept": n_img})
        print(f"  {stem:<30} {npages:>3}p  {kind:<14} +{n_img} imgs")
        doc.close()

    with open(os.path.join(dst, "_index.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n{len(summary)} PDFs → {dst}")


if __name__ == "__main__":
    main()
