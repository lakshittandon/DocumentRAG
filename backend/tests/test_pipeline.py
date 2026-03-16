from __future__ import annotations

from pathlib import Path
import tempfile
import time
import unittest

from app.core.config import Settings
from app.services.models import HashedEmbeddingModel, HeuristicChatModel, OverlapVerifier
from app.services.pipeline import RAGPipeline
from app.services.storage import AuditLogStore, KnowledgeBaseStore


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        corpus_dir = root / "corpus"
        uploads_dir = root / "uploads"
        corpus_dir.mkdir()
        uploads_dir.mkdir()

        (corpus_dir / "doc1.txt").write_text(
            "Reliable answers should cite source passages and refuse unsupported claims.",
            encoding="utf-8",
        )

        self.settings = Settings(
            app_name="Test",
            app_version="0.1.0",
            jwt_secret="secret",
            access_token_expiry_minutes=60,
            upload_dir=uploads_dir,
            corpus_dir=corpus_dir,
            dense_top_k=10,
            bm25_top_k=10,
            rerank_top_k=10,
            answer_top_k=5,
            chunk_size=150,
            chunk_overlap=20,
            refusal_text="Not found in the provided documents.",
        )
        self.pipeline = RAGPipeline(
            settings=self.settings,
            store=KnowledgeBaseStore(),
            audit_store=AuditLogStore(),
            embedder=HashedEmbeddingModel(),
            chat_model=HeuristicChatModel(),
            verifier=OverlapVerifier(),
        )
        self.pipeline.bootstrap()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_duplicate_document_is_not_reingested(self) -> None:
        original = self.pipeline.list_documents()[0]
        duplicate = self.pipeline.ingest_file(Path(original.source_path), actor="tester")
        self.assertEqual(original.id, duplicate.id)
        self.assertEqual(len(self.pipeline.list_documents()), 1)

    def test_negative_query_uses_refusal(self) -> None:
        result = self.pipeline.query("What does the corpus say about orbital mechanics?", actor="tester")
        self.assertEqual(result.answer, self.settings.refusal_text)

    def test_delete_document_removes_it_from_corpus(self) -> None:
        document = self.pipeline.list_documents()[0]
        deleted = self.pipeline.delete_document(document.id, actor="tester")
        self.assertEqual(deleted.id, document.id)
        self.assertEqual(len(self.pipeline.list_documents()), 0)
        self.assertFalse(Path(document.source_path).exists())

    def test_queue_ingest_file_returns_processing_then_indexes(self) -> None:
        upload_path = self.settings.upload_dir / "queued.txt"
        upload_path.write_text("Queued upload should become indexed after background processing.", encoding="utf-8")
        queued = self.pipeline.queue_ingest_file(upload_path, actor="tester", content_type="text/plain")
        self.assertEqual(queued.status, "processing")

        for _ in range(50):
            current = self.pipeline.list_documents()[0]
            if current.status == "indexed":
                break
            time.sleep(0.02)
        current = self.pipeline.list_documents()[0]
        self.assertEqual(current.status, "indexed")
        self.assertGreaterEqual(current.chunk_count, 1)


if __name__ == "__main__":
    unittest.main()
