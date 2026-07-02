from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import os

from app.services.chunking import ParsedPage, infer_section


class UnsupportedDocumentError(RuntimeError):
    pass


@dataclass(slots=True)
class ParsedDocument:
    filename: str
    content_type: str
    checksum: str
    source_path: str
    pages: list[ParsedPage]


TEXT_CONTENT_TYPES = {
    ".txt": "text/plain",
    ".md": "text/markdown",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        while True:
            block = file_handle.read(8192)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _parse_text_file(path: Path) -> ParsedDocument:
    text = path.read_text(encoding="utf-8")
    normalized = " ".join(text.replace("\t", " ").split())
    section = infer_section(text, "Document Body")
    return ParsedDocument(
        filename=path.name,
        content_type=TEXT_CONTENT_TYPES[path.suffix.lower()],
        checksum=sha256_file(path),
        source_path=str(path),
        pages=[ParsedPage(page_number=1, text=normalized, section=section)],
    )


def _parse_pdf_file(path: Path) -> ParsedDocument:
    try:
        return _parse_pdf_with_pdfplumber(path)
    except ImportError:
        pass

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise UnsupportedDocumentError("PDF support requires the pypdf dependency.") from exc

    reader = PdfReader(str(path))
    pages: list[ParsedPage] = []
    for index, page in enumerate(reader.pages, start=1):
        extracted = (page.extract_text() or "").strip()
        if not extracted:
            continue
        normalized = " ".join(extracted.replace("\t", " ").split())
        pages.append(
            ParsedPage(
                page_number=index,
                text=normalized,
                section=infer_section(extracted, f"Page {index}"),
            )
        )

    if not pages:
        raise UnsupportedDocumentError(
            "Scanned or image-only PDFs are not supported in v1 because no text could be extracted."
        )

    return ParsedDocument(
        filename=path.name,
        content_type="application/pdf",
        checksum=sha256_file(path),
        source_path=str(path),
        pages=pages,
    )


def _parse_pdf_with_pdfplumber(path: Path) -> ParsedDocument:
    import pdfplumber

    pages: list[ParsedPage] = []
    enable_ocr = os.getenv("ENABLE_OCR", "true").lower() in {"1", "true", "yes"}
    ocr_language = os.getenv("OCR_LANGUAGE", "eng")
    with pdfplumber.open(str(path)) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            extracted = (page.extract_text() or "").strip()
            table_blocks: list[str] = []
            for table_index, table in enumerate(page.extract_tables() or [], start=1):
                flattened = _flatten_table(table)
                if flattened:
                    table_blocks.append(f"TABLE {table_index}: {flattened}")

            combined = "\n".join(part for part in [extracted, *table_blocks] if part).strip()
            if not combined and enable_ocr:
                combined = _ocr_pdf_page(page, language=ocr_language)
            if not combined:
                continue
            normalized = " ".join(combined.replace("\t", " ").split())
            pages.append(
                ParsedPage(
                    page_number=index,
                    text=normalized,
                    section=infer_section(combined, f"Page {index}"),
                )
            )

    if not pages:
        raise UnsupportedDocumentError(
            "Scanned or image-only PDFs are not supported in v1 because no text could be extracted."
        )

    return ParsedDocument(
        filename=path.name,
        content_type="application/pdf",
        checksum=sha256_file(path),
        source_path=str(path),
        pages=pages,
    )


def _ocr_pdf_page(page, language: str) -> str:
    try:
        import pytesseract
    except ImportError as exc:
        raise UnsupportedDocumentError("OCR support requires the pytesseract dependency.") from exc

    try:
        image = page.to_image(resolution=200).original
        return " ".join(pytesseract.image_to_string(image, lang=language).split())
    except pytesseract.TesseractNotFoundError as exc:
        raise UnsupportedDocumentError(
            "OCR support requires the Tesseract system package to be installed."
        ) from exc
    except Exception as exc:
        raise UnsupportedDocumentError(f"OCR failed for a scanned PDF page: {exc}") from exc


def _flatten_table(table: list[list[str | None]]) -> str:
    rows: list[str] = []
    for row in table:
        cells = [" ".join((cell or "").split()) for cell in row]
        cells = [cell for cell in cells if cell]
        if cells:
            rows.append(" | ".join(cells))
    return " ; ".join(rows)


def parse_document(path: Path) -> ParsedDocument:
    suffix = path.suffix.lower()
    if suffix in TEXT_CONTENT_TYPES:
        return _parse_text_file(path)
    if suffix == ".pdf":
        return _parse_pdf_file(path)
    raise UnsupportedDocumentError(f"Unsupported file type: {suffix or 'unknown'}")
