"""One-off extraction for TCC doc analysis. Not part of product runtime."""
from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from pypdf import PdfReader

TCC = Path(__file__).resolve().parent
OUT = TCC / "_extracted"


def extract_docx(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paras: list[str] = []
    for para in root.findall(".//w:p", ns):
        texts = [t.text or "" for t in para.findall(".//w:t", ns)]
        line = "".join(texts).strip()
        if line:
            paras.append(line)
    return paras


def extract_pdf_pages(path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(path))
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append((i, text))
    return pages


def find_chapter_starts(pages: list[tuple[int, str]]) -> list[tuple[int, str, str]]:
    """Heuristic: lines that look like chapter headings."""
    hits: list[tuple[int, str, str]] = []
    pat = re.compile(
        r"(?i)(cap[ií]tulo\s+\d+|^\s*\d+\s+[\w\s]{5,80}$|DESENVOLVIMENTO|RESULTADOS|CONCLUS)",
        re.M,
    )
    for num, text in pages:
        for m in pat.finditer(text):
            snippet = m.group(0).strip().replace("\n", " ")[:120]
            hits.append((num, snippet, text[:400].replace("\n", " ")))
    return hits


def main() -> None:
    OUT.mkdir(exist_ok=True)

    docx_path = TCC / "Report 6 - Resultados.docx"
    paras = extract_docx(docx_path)
    (OUT / "report6_paragraphs.txt").write_text(
        "\n\n".join(f"[{i:04d}] {p}" for i, p in enumerate(paras)),
        encoding="utf-8",
    )

    # Outline: headings-like lines in docx
    outline: list[str] = []
    for i, p in enumerate(paras):
        if re.match(r"^(CAPÍTULO|Capítulo|\d+\.\d*\.?\s|[IVX]+\.\s)", p, re.I):
            outline.append(f"[{i:04d}] {p}")
        elif len(p) < 100 and p.isupper() and len(p) > 8:
            outline.append(f"[{i:04d}] {p}")
    (OUT / "report6_outline.txt").write_text("\n".join(outline), encoding="utf-8")

    pdfs = [
        "ETL-DATAHUB AUTOMAÇÃO E INTEGRAÇÃO DE DADOS.pdf",
        "SOFTWARE DE CODIFICAÇÃO PARA ANÁLISES QUALITATIVA.pdf",
    ]
    for name in pdfs:
        path = TCC / name
        slug = re.sub(r"[^\w]+", "-", name[:40]).strip("-").lower()
        pages = extract_pdf_pages(path)
        full = "\n\n".join(f"--- page {n} ---\n{t}" for n, t in pages)
        (OUT / f"{slug}_full.txt").write_text(full, encoding="utf-8")
        hits = find_chapter_starts(pages)
        (OUT / f"{slug}_headings.txt").write_text(
            "\n".join(f"p.{n}: {snip}" for n, snip, _ in hits[:80]),
            encoding="utf-8",
        )
        print(name, "pages", len(pages), "docx paras", len(paras) if name == pdfs[0] else "")


if __name__ == "__main__":
    main()
