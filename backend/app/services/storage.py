from __future__ import annotations

from collections import OrderedDict
import json
from dataclasses import replace
from typing import Any, Iterable
from uuid import uuid4

from app.core.security import hash_password
from app.domain.types import AuditLogEntry, ChunkRecord, DocumentRecord, UserAccount, utc_now_iso


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

    def get_documents_by_logical_name(self, logical_name: str) -> list[DocumentRecord]:
        return [
            document
            for document in self._documents.values()
            if document.logical_name == logical_name
        ]

    def get_latest_document_by_logical_name(self, logical_name: str) -> DocumentRecord | None:
        versions = self.get_documents_by_logical_name(logical_name)
        if not versions:
            return None
        return max(versions, key=lambda document: document.version)

    def save_document(self, document: DocumentRecord, chunks: list) -> DocumentRecord:
        stored = replace(document, chunk_count=len(chunks), updated_at=utc_now_iso())
        self._documents[stored.id] = stored
        self._chunks_by_document[stored.id] = list(chunks)
        return stored

    def replace_document_chunks(self, document_id: str, chunks: list) -> DocumentRecord:
        document = self._documents[document_id]
        updated = replace(document, chunk_count=len(chunks), updated_at=utc_now_iso())
        self._documents[document_id] = updated
        self._chunks_by_document[document_id] = list(chunks)
        return updated

    def update_document(self, document: DocumentRecord) -> DocumentRecord:
        updated = replace(document, updated_at=utc_now_iso())
        self._documents[updated.id] = updated
        self._chunks_by_document.setdefault(updated.id, [])
        return updated

    def delete_document(self, document_id: str) -> DocumentRecord | None:
        document = self._documents.pop(document_id, None)
        if document is None:
            return None
        self._chunks_by_document.pop(document_id, None)
        return document

    def all_chunks(self) -> list:
        chunks: list = []
        for document_chunks in self._chunks_by_document.values():
            chunks.extend(document_chunks)
        return chunks

    def document_chunks(self, document_id: str) -> list:
        return list(self._chunks_by_document.get(document_id, []))

    def create_document_id(self) -> str:
        return str(uuid4())

    def save_document_file(self, document_id: str, filename: str, content_type: str, content: bytes) -> None:
        return None

    def get_document_file(self, document_id: str) -> bytes | None:
        return None


class PostgresKnowledgeBaseStore(KnowledgeBaseStore):
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._ensure_schema()

    def _connect(self):
        return _connect_postgres(self.database_url)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    page_count INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    logical_name TEXT,
                    version INTEGER NOT NULL,
                    parent_document_id TEXT,
                    previous_version_id TEXT,
                    owner_username TEXT NOT NULL,
                    visibility TEXT NOT NULL,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    document_name TEXT NOT NULL,
                    text TEXT NOT NULL,
                    page INTEGER NOT NULL,
                    section TEXT NOT NULL,
                    token_count INTEGER NOT NULL,
                    source_path TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_files (
                    document_id TEXT PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
                    filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    content BYTEA NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_checksum ON documents(checksum)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_logical_name ON documents(logical_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)")

    def list_documents(self) -> list[DocumentRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, filename, content_type, checksum, source_path, status, page_count, chunk_count,
                       logical_name, version, parent_document_id, previous_version_id, owner_username,
                       visibility, error_message, created_at, updated_at
                FROM documents
                ORDER BY updated_at DESC
                """
            ).fetchall()
        return [self._row_to_document(row) for row in rows]

    def get_document(self, document_id: str) -> DocumentRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, filename, content_type, checksum, source_path, status, page_count, chunk_count,
                       logical_name, version, parent_document_id, previous_version_id, owner_username,
                       visibility, error_message, created_at, updated_at
                FROM documents
                WHERE id = %s
                """,
                (document_id,),
            ).fetchone()
        return self._row_to_document(row) if row else None

    def get_document_by_checksum(self, checksum: str) -> DocumentRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, filename, content_type, checksum, source_path, status, page_count, chunk_count,
                       logical_name, version, parent_document_id, previous_version_id, owner_username,
                       visibility, error_message, created_at, updated_at
                FROM documents
                WHERE checksum = %s
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (checksum,),
            ).fetchone()
        return self._row_to_document(row) if row else None

    def get_documents_by_logical_name(self, logical_name: str) -> list[DocumentRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, filename, content_type, checksum, source_path, status, page_count, chunk_count,
                       logical_name, version, parent_document_id, previous_version_id, owner_username,
                       visibility, error_message, created_at, updated_at
                FROM documents
                WHERE logical_name = %s
                ORDER BY version DESC
                """,
                (logical_name,),
            ).fetchall()
        return [self._row_to_document(row) for row in rows]

    def save_document(self, document: DocumentRecord, chunks: list) -> DocumentRecord:
        stored = replace(document, chunk_count=len(chunks), updated_at=utc_now_iso())
        with self._connect() as conn:
            self._upsert_document(conn, stored)
            conn.execute("DELETE FROM chunks WHERE document_id = %s", (stored.id,))
            self._insert_chunks(conn, chunks)
        return stored

    def replace_document_chunks(self, document_id: str, chunks: list) -> DocumentRecord:
        document = self.get_document(document_id)
        if document is None:
            raise KeyError(document_id)
        updated = replace(document, chunk_count=len(chunks), updated_at=utc_now_iso())
        with self._connect() as conn:
            self._upsert_document(conn, updated)
            conn.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))
            self._insert_chunks(conn, chunks)
        return updated

    def update_document(self, document: DocumentRecord) -> DocumentRecord:
        updated = replace(document, updated_at=utc_now_iso())
        with self._connect() as conn:
            self._upsert_document(conn, updated)
        return updated

    def delete_document(self, document_id: str) -> DocumentRecord | None:
        document = self.get_document(document_id)
        if document is None:
            return None
        with self._connect() as conn:
            conn.execute("DELETE FROM documents WHERE id = %s", (document_id,))
        return document

    def all_chunks(self) -> list:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, document_id, document_name, text, page, section, token_count, source_path
                FROM chunks
                """
            ).fetchall()
        return [self._row_to_chunk(row) for row in rows]

    def document_chunks(self, document_id: str) -> list:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, document_id, document_name, text, page, section, token_count, source_path
                FROM chunks
                WHERE document_id = %s
                """,
                (document_id,),
            ).fetchall()
        return [self._row_to_chunk(row) for row in rows]

    def save_document_file(self, document_id: str, filename: str, content_type: str, content: bytes) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO document_files (document_id, filename, content_type, content, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (document_id) DO UPDATE SET
                    filename = EXCLUDED.filename,
                    content_type = EXCLUDED.content_type,
                    content = EXCLUDED.content,
                    updated_at = EXCLUDED.updated_at
                """,
                (document_id, filename, content_type, content, utc_now_iso()),
            )

    def get_document_file(self, document_id: str) -> bytes | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT content FROM document_files WHERE document_id = %s",
                (document_id,),
            ).fetchone()
        return bytes(row[0]) if row else None

    def _upsert_document(self, conn, document: DocumentRecord) -> None:
        conn.execute(
            """
            INSERT INTO documents (
                id, filename, content_type, checksum, source_path, status, page_count, chunk_count,
                logical_name, version, parent_document_id, previous_version_id, owner_username,
                visibility, error_message, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                filename = EXCLUDED.filename,
                content_type = EXCLUDED.content_type,
                checksum = EXCLUDED.checksum,
                source_path = EXCLUDED.source_path,
                status = EXCLUDED.status,
                page_count = EXCLUDED.page_count,
                chunk_count = EXCLUDED.chunk_count,
                logical_name = EXCLUDED.logical_name,
                version = EXCLUDED.version,
                parent_document_id = EXCLUDED.parent_document_id,
                previous_version_id = EXCLUDED.previous_version_id,
                owner_username = EXCLUDED.owner_username,
                visibility = EXCLUDED.visibility,
                error_message = EXCLUDED.error_message,
                updated_at = EXCLUDED.updated_at
            """,
            (
                document.id,
                document.filename,
                document.content_type,
                document.checksum,
                document.source_path,
                document.status,
                document.page_count,
                document.chunk_count,
                document.logical_name,
                document.version,
                document.parent_document_id,
                document.previous_version_id,
                document.owner_username,
                document.visibility,
                document.error_message,
                document.created_at,
                document.updated_at,
            ),
        )

    def _insert_chunks(self, conn, chunks: list) -> None:
        for chunk in chunks:
            conn.execute(
                """
                INSERT INTO chunks (id, document_id, document_name, text, page, section, token_count, source_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    chunk.id,
                    chunk.document_id,
                    chunk.document_name,
                    chunk.text,
                    chunk.page,
                    chunk.section,
                    chunk.token_count,
                    chunk.source_path,
                ),
            )

    @staticmethod
    def _row_to_document(row) -> DocumentRecord:
        return DocumentRecord(
            id=row[0],
            filename=row[1],
            content_type=row[2],
            checksum=row[3],
            source_path=row[4],
            status=row[5],
            page_count=row[6],
            chunk_count=row[7],
            logical_name=row[8],
            version=row[9],
            parent_document_id=row[10],
            previous_version_id=row[11],
            owner_username=row[12],
            visibility=row[13],
            error_message=row[14],
            created_at=row[15],
            updated_at=row[16],
        )

    @staticmethod
    def _row_to_chunk(row) -> ChunkRecord:
        return ChunkRecord(
            id=row[0],
            document_id=row[1],
            document_name=row[2],
            text=row[3],
            page=row[4],
            section=row[5],
            token_count=row[6],
            source_path=row[7],
        )


class AuditLogStore:
    def __init__(self) -> None:
        self._entries: list[AuditLogEntry] = []

    def append(
        self,
        actor: str,
        action: str,
        detail: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            id=str(uuid4()),
            actor=actor,
            action=action,
            detail=detail,
            metadata=metadata or {},
        )
        self._entries.insert(0, entry)
        return entry

    def list_entries(self) -> list[AuditLogEntry]:
        return list(self._entries)

    def extend_seed(self, entries: Iterable[AuditLogEntry]) -> None:
        for entry in entries:
            self._entries.insert(0, entry)


class PostgresAuditLogStore(AuditLogStore):
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._ensure_schema()

    def _connect(self):
        return _connect_postgres(self.database_url)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    metadata JSONB NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC)")

    def append(
        self,
        actor: str,
        action: str,
        detail: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            id=str(uuid4()),
            actor=actor,
            action=action,
            detail=detail,
            metadata=metadata or {},
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (id, actor, action, detail, metadata, created_at)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                """,
                (
                    entry.id,
                    entry.actor,
                    entry.action,
                    entry.detail,
                    json.dumps(entry.metadata),
                    entry.created_at,
                ),
            )
        return entry

    def list_entries(self) -> list[AuditLogEntry]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, actor, action, detail, metadata, created_at
                FROM audit_logs
                ORDER BY created_at DESC
                LIMIT 500
                """
            ).fetchall()
        return [
            AuditLogEntry(
                id=row[0],
                actor=row[1],
                action=row[2],
                detail=row[3],
                metadata=row[4] if isinstance(row[4], dict) else json.loads(row[4]),
                created_at=row[5],
            )
            for row in rows
        ]

    def extend_seed(self, entries: Iterable[AuditLogEntry]) -> None:
        for entry in entries:
            self.append(entry.actor, entry.action, entry.detail, entry.metadata)


def _normalize_postgres_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return f"postgresql://{database_url.removeprefix('postgres://')}"
    return database_url


def _connect_postgres(database_url: str):
    import time

    import psycopg

    normalized_url = _normalize_postgres_url(database_url)
    last_error: Exception | None = None
    for _ in range(15):
        try:
            return psycopg.connect(normalized_url)
        except psycopg.OperationalError as exc:
            last_error = exc
            time.sleep(1)
    if last_error:
        raise last_error
    return psycopg.connect(normalized_url)
