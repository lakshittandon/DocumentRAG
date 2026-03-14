from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable
from uuid import uuid4

from app.domain.types import ChunkRecord


SECTION_PATTERN = re.compile(r"^(#{1,6}\s+.+|[A-Z][A-Z0-9\s]{4,}|[0-9]+\.\s+.+)$")


@dataclass(slots=True)
class ParsedPage:
    page_number: int
    text: str
    section: str


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", text.lower())


def infer_section(text: str, fallback: str) -> str:
    for line in text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        if SECTION_PATTERN.match(cleaned):
            return cleaned[:120]
    return fallback


def build_chunks(
    document_id: str,
    document_name: str,
    source_path: str,
    pages: Iterable[ParsedPage],
    chunk_size: int,
    chunk_overlap: int,
) -> list[ChunkRecord]:
    chunks: list[ChunkRecord] = []

    for page in pages:
        page_tokens = page.text.split()
        if not page_tokens:
            continue

        step = max(chunk_size - chunk_overlap, 1)
        for start in range(0, len(page_tokens), step):
            window = page_tokens[start : start + chunk_size]
            if not window:
                continue
            chunk_text = " ".join(window).strip()
            if not chunk_text:
                continue
            chunks.append(
                ChunkRecord(
                    id=str(uuid4()),
                    document_id=document_id,
                    document_name=document_name,
                    text=chunk_text,
                    page=page.page_number,
                    section=page.section,
                    token_count=len(window),
                    source_path=source_path,
                )
            )

    return chunks

