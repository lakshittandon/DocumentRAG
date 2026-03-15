from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import threading

from app.core.config import Settings
from app.domain.types import Citation, DocumentRecord, QueryResult
from app.services.chunking import build_chunks
from app.services.evaluation import EvaluationRunner, load_benchmark
from app.services.models import ChatModel, EmbeddingModel, Verifier
from app.services.parsing import ParsedDocument, UnsupportedDocumentError, parse_document, sha256_file
from app.services.retrieval import RetrievalEngine
from app.services.storage import AuditLogStore, EvaluationStore, KnowledgeBaseStore


class RAGPipeline:
    def __init__(
        self,
        settings: Settings,
        store: KnowledgeBaseStore,
        audit_store: AuditLogStore,
        evaluation_store: EvaluationStore,
        embedder: EmbeddingModel,
        chat_model: ChatModel,
        verifier: Verifier,
    ) -> None:
        self.settings = settings
        self.store = store
        self.audit_store = audit_store
        self.evaluation_store = evaluation_store
        self.chat_model = chat_model
        self.verifier = verifier
        self.retrieval_engine = RetrievalEngine(embedder)
        self.evaluation_runner = EvaluationRunner(refusal_text=settings.refusal_text)
        self._lock = threading.RLock()

    def bootstrap(self) -> None:
        self.settings.ensure_directories()
        with self._lock:
            if self.store.list_documents():
                self.retrieval_engine.update(self.store.all_chunks())
                return

            for file_path in sorted(self.settings.corpus_dir.glob("*")):
                if not file_path.is_file():
                    continue
                try:
                    self.ingest_file(file_path, actor="system", allow_duplicates=False)
                except UnsupportedDocumentError:
                    continue

    def ingest_file(self, path: Path, actor: str, allow_duplicates: bool = False) -> DocumentRecord:
        with self._lock:
            parsed = parse_document(path)
            existing = self.store.get_document_by_checksum(parsed.checksum)
            if existing and not allow_duplicates:
                self.audit_store.append(actor=actor, action="document.duplicate", detail=f"Skipped duplicate {path.name}.")
                return existing

            document = self._build_document_record(parsed)
            chunks = build_chunks(
                document_id=document.id,
                document_name=document.filename,
                source_path=document.source_path,
                pages=parsed.pages,
                chunk_size=self.settings.chunk_size,
                chunk_overlap=self.settings.chunk_overlap,
            )

            stored = self.store.save_document(document, chunks)
            self.retrieval_engine.update(self.store.all_chunks())
            self.audit_store.append(
                actor=actor,
                action="document.ingest",
                detail=f"Ingested {stored.filename} with {stored.chunk_count} chunks.",
            )
            return stored

    def queue_ingest_file(self, path: Path, actor: str, content_type: str) -> DocumentRecord:
        checksum = sha256_file(path)
        with self._lock:
            existing = self.store.get_document_by_checksum(checksum)
            if existing:
                path.unlink(missing_ok=True)
                self.audit_store.append(actor=actor, action="document.duplicate", detail=f"Skipped duplicate {path.name}.")
                return existing

            document = DocumentRecord(
                id=self.store.create_document_id(),
                filename=path.name,
                content_type=content_type or "application/octet-stream",
                checksum=checksum,
                source_path=str(path),
                status="processing",
                page_count=0,
                chunk_count=0,
                error_message=None,
            )
            placeholder = self.store.save_document(document, [])
            self.audit_store.append(
                actor=actor,
                action="document.ingest_queued",
                detail=f"Queued {placeholder.filename} for background indexing.",
            )

        worker = threading.Thread(
            target=self._complete_ingestion_job,
            args=(placeholder.id, actor),
            daemon=True,
        )
        worker.start()
        return placeholder

    def _complete_ingestion_job(self, document_id: str, actor: str) -> None:
        with self._lock:
            document = self.store.get_document(document_id)
        if not document:
            return

        try:
            parsed = parse_document(Path(document.source_path))
            chunks = build_chunks(
                document_id=document.id,
                document_name=document.filename,
                source_path=document.source_path,
                pages=parsed.pages,
                chunk_size=self.settings.chunk_size,
                chunk_overlap=self.settings.chunk_overlap,
            )

            with self._lock:
                finalized = replace(
                    document,
                    content_type=parsed.content_type,
                    checksum=parsed.checksum,
                    status="indexed",
                    page_count=len(parsed.pages),
                    chunk_count=len(chunks),
                    error_message=None,
                )
                self.store.save_document(finalized, chunks)
                self.retrieval_engine.update(self.store.all_chunks())
                self.audit_store.append(
                    actor=actor,
                    action="document.ingest",
                    detail=f"Ingested {finalized.filename} with {finalized.chunk_count} chunks.",
                )
        except Exception as exc:
            with self._lock:
                failed = replace(
                    document,
                    status="failed",
                    page_count=0,
                    chunk_count=0,
                    error_message=str(exc),
                )
                self.store.update_document(failed)
                self.audit_store.append(
                    actor=actor,
                    action="document.ingest_failed",
                    detail=f"Failed to ingest {document.filename}: {exc}",
                )

    def reindex_document(self, document_id: str, actor: str) -> DocumentRecord:
        with self._lock:
            document = self.store.get_document(document_id)
            if not document:
                raise ValueError("Document not found.")

            parsed = parse_document(Path(document.source_path))
            chunks = build_chunks(
                document_id=document.id,
                document_name=document.filename,
                source_path=document.source_path,
                pages=parsed.pages,
                chunk_size=self.settings.chunk_size,
                chunk_overlap=self.settings.chunk_overlap,
            )
            updated = self.store.replace_document_chunks(document.id, chunks)
            self.retrieval_engine.update(self.store.all_chunks())
            self.audit_store.append(
                actor=actor,
                action="document.reindex",
                detail=f"Reindexed {document.filename} with {len(chunks)} chunks.",
            )
            return updated

    def delete_document(self, document_id: str, actor: str) -> DocumentRecord:
        with self._lock:
            document = self.store.get_document(document_id)
            if not document:
                raise ValueError("Document not found.")

            deleted = self.store.delete_document(document_id)
            self.retrieval_engine.update(self.store.all_chunks())

        source_path = Path(document.source_path)
        if source_path.exists():
            source_path.unlink()

        self.audit_store.append(
            actor=actor,
            action="document.delete",
            detail=f"Deleted {document.filename} from the corpus.",
        )
        return deleted or document

    def list_documents(self) -> list[DocumentRecord]:
        with self._lock:
            return self.store.list_documents()

    def query(self, question: str, actor: str) -> QueryResult:
        with self._lock:
            dense_hits = self.retrieval_engine.dense_retrieve(question, self.settings.dense_top_k)
            keyword_hits = self.retrieval_engine.keyword_retrieve(question, self.settings.bm25_top_k)
            trace = self.retrieval_engine.fuse_and_rerank(
                query=question,
                dense_hits=dense_hits,
                keyword_hits=keyword_hits,
                rerank_top_k=self.settings.rerank_top_k,
                answer_top_k=self.settings.answer_top_k,
            )

            chunk_map = {chunk.id: chunk for chunk in self.store.all_chunks()}
            evidence_chunks = [chunk_map[hit.chunk_id] for hit in trace.reranked_hits if hit.chunk_id in chunk_map]
        answer = self.chat_model.answer(question, evidence_chunks, self.settings.refusal_text)
        if answer == self.settings.refusal_text:
            verification = self.verifier.verify("", evidence_chunks)
            citations: list[Citation] = []
            support_score = 1.0
            unsupported_sentences: list[str] = []
        else:
            verification = self.verifier.verify(answer, evidence_chunks)
            citations = [
                Citation(
                    chunk_id=hit.chunk_id,
                    document_id=hit.document_id,
                    document_name=hit.document_name,
                    page=hit.page,
                    section=hit.section,
                    snippet=f"{hit.text[:160]}...",
                    score=hit.score,
                )
                for hit in trace.reranked_hits
            ]
            support_score = verification.support_score
            unsupported_sentences = verification.unsupported_sentences

        result = QueryResult(
            answer=answer,
            citations=citations,
            support_score=support_score,
            unsupported_sentences=unsupported_sentences,
            retrieval_trace=trace,
        )
        self.audit_store.append(actor=actor, action="query.run", detail=f"Question: {question}")
        return result

    def run_benchmark(self, actor: str):
        benchmark = load_benchmark(self.settings.benchmark_path)
        results = [self.query(sample.question, actor=actor) for sample in benchmark]
        run = self.evaluation_runner.build_run(benchmark, results)
        with self._lock:
            self.evaluation_store.add(run)
        self.audit_store.append(
            actor=actor,
            action="evaluation.run",
            detail=f"Completed evaluation run {run.id} across {run.sample_count} samples.",
        )
        return run

    def list_evaluations(self):
        with self._lock:
            return self.evaluation_store.list_runs()

    def list_logs(self):
        with self._lock:
            return self.audit_store.list_entries()

    def _build_document_record(self, parsed: ParsedDocument) -> DocumentRecord:
        return DocumentRecord(
            id=self.store.create_document_id(),
            filename=parsed.filename,
            content_type=parsed.content_type,
            checksum=parsed.checksum,
            source_path=parsed.source_path,
            status="indexed",
            page_count=len(parsed.pages),
            chunk_count=0,
        )
