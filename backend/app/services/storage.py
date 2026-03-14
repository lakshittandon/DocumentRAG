from __future__ import annotations

from collections import OrderedDict
from dataclasses import replace
from typing import Iterable
from uuid import uuid4

from app.core.security import hash_password
from app.domain.types import AuditLogEntry, DocumentRecord, EvaluationRun, UserAccount, utc_now_iso


class UserStore:
    def __init__(self) -> None:
        self._users = {
            "admin": UserAccount(
                username="admin",
                full_name="Lakshit Tandon",
                role="admin",
                hashed_password=hash_password("admin123"),
            )
        }

    def get(self, username: str) -> UserAccount | None:
        return self._users.get(username)


class KnowledgeBaseStore:
    def __init__(self) -> None:
        self._documents: OrderedDict[str, DocumentRecord] = OrderedDict()
        self._chunks_by_document: dict[str, list] = {}

    def list_documents(self) -> list[DocumentRecord]:
        return list(reversed(list(self._documents.values())))

    def get_document(self, document_id: str) -> DocumentRecord | None:
        return self._documents.get(document_id)

    def get_document_by_checksum(self, checksum: str) -> DocumentRecord | None:
        for document in self._documents.values():
            if document.checksum == checksum:
                return document
        return None

    def save_document(self, document: DocumentRecord, chunks: list) -> DocumentRecord:
        stored = replace(document, chunk_count=len(chunks))
        self._documents[stored.id] = stored
        self._chunks_by_document[stored.id] = list(chunks)
        return stored

    def replace_document_chunks(self, document_id: str, chunks: list) -> DocumentRecord:
        document = self._documents[document_id]
        updated = replace(document, chunk_count=len(chunks), updated_at=utc_now_iso())
        self._documents[document_id] = updated
        self._chunks_by_document[document_id] = list(chunks)
        return updated

    def all_chunks(self) -> list:
        chunks: list = []
        for document_chunks in self._chunks_by_document.values():
            chunks.extend(document_chunks)
        return chunks

    def document_chunks(self, document_id: str) -> list:
        return list(self._chunks_by_document.get(document_id, []))

    def create_document_id(self) -> str:
        return str(uuid4())


class EvaluationStore:
    def __init__(self) -> None:
        self._runs: list[EvaluationRun] = []

    def add(self, run: EvaluationRun) -> EvaluationRun:
        self._runs.insert(0, run)
        return run

    def list_runs(self) -> list[EvaluationRun]:
        return list(self._runs)


class AuditLogStore:
    def __init__(self) -> None:
        self._entries: list[AuditLogEntry] = []

    def append(self, actor: str, action: str, detail: str) -> AuditLogEntry:
        entry = AuditLogEntry(id=str(uuid4()), actor=actor, action=action, detail=detail)
        self._entries.insert(0, entry)
        return entry

    def list_entries(self) -> list[AuditLogEntry]:
        return list(self._entries)

    def extend_seed(self, entries: Iterable[AuditLogEntry]) -> None:
        for entry in entries:
            self._entries.insert(0, entry)
