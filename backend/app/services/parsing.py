from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib

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


def parse_document(path: Path) -> ParsedDocument:
    suffix = path.suffix.lower()
    if suffix in TEXT_CONTENT_TYPES:
        return _parse_text_file(path)
    if suffix == ".pdf":
        return _parse_pdf_file(path)
    raise UnsupportedDocumentError(f"Unsupported file type: {suffix or 'unknown'}")

