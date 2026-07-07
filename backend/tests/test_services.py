from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from app.domain.types import ChunkRecord
from app.services.chunking import ParsedPage, build_chunks
from app.services.auth import AuthService
from app.services.models import HashedEmbeddingModel, HeuristicChatModel, OllamaChatModel, OverlapVerifier
from app.services.parsing import parse_document
from app.services.retrieval import RetrievalEngine
from app.services.storage import AuditLogStore, UserStore


class AuthServiceTests(unittest.TestCase):
    def test_register_creates_user_and_allows_login(self) -> None:
        audit_store = AuditLogStore()
        auth_service = AuthService(
            user_store=UserStore(),
            audit_store=audit_store,
            secret="secret",
            expiry_minutes=60,
        )

        token = auth_service.register("Teacher.User", "Teacher User", "secret123")
        self.assertTrue(token)

        user = auth_service.get_user_from_token(token)
        self.assertEqual(user.username, "teacher.user")
        self.assertEqual(user.role, "user")

        login_token = auth_service.authenticate("TEACHER.USER", "secret123")
        self.assertTrue(login_token)

    def test_register_rejects_duplicate_username(self) -> None:
        auth_service = AuthService(
            user_store=UserStore(),
            audit_store=AuditLogStore(),
            secret="secret",
            expiry_minutes=60,
        )
        auth_service.register("student", "Student User", "secret123")

        with self.assertRaises(ValueError):
            auth_service.register("Student", "Student User", "secret123")


class ParsingAndChunkingTests(unittest.TestCase):
    def test_parse_text_document(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "notes.txt"
            file_path.write_text("INTRODUCTION\nReliable RAG needs evidence and citations.", encoding="utf-8")
            parsed = parse_document(file_path)
            self.assertEqual(parsed.filename, "notes.txt")
            self.assertEqual(parsed.pages[0].section, "INTRODUCTION")

    @unittest.skipUnless(shutil.which("tesseract"), "Tesseract OCR binary is not installed")
    def test_parse_scanned_pdf_with_ocr(self) -> None:
        from PIL import Image, ImageDraw

        with tempfile.TemporaryDirectory() as temp_dir:
            image = Image.new("RGB", (1200, 700), "white")
            draw = ImageDraw.Draw(image)
            draw.text((80, 120), "SCANNED POLICY", fill="black")
            draw.text((80, 220), "Remote work is allowed for two days per week.", fill="black")

            file_path = Path(temp_dir) / "scanned_policy.pdf"
            image.save(file_path, "PDF", resolution=150.0)

            parsed = parse_document(file_path)

            self.assertEqual(parsed.filename, "scanned_policy.pdf")
            self.assertEqual(len(parsed.pages), 1)
            self.assertIn("Remote work", parsed.pages[0].text)
            self.assertIn("two days", parsed.pages[0].text)

    def test_build_chunks_creates_overlap(self) -> None:
        page = ParsedPage(
            page_number=1,
            text=" ".join(f"token{i}" for i in range(900)),
            section="Body",
        )
        chunks = build_chunks(
            document_id="doc-1",
            document_name="demo.txt",
            source_path="/tmp/demo.txt",
            pages=[page],
            chunk_size=300,
            chunk_overlap=75,
        )
        self.assertGreater(len(chunks), 2)
        self.assertEqual(chunks[0].page, 1)


class RetrievalAndVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.chunks = [
            ChunkRecord(
                id="c1",
                document_id="d1",
                document_name="rag_overview.txt",
                text="Hybrid retrieval combines dense retrieval and BM25 for stronger recall.",
                page=1,
                section="Overview",
                token_count=10,
                source_path="/tmp/rag_overview.txt",
            ),
            ChunkRecord(
                id="c2",
                document_id="d2",
                document_name="evaluation_guidelines.txt",
                text="Evaluation should report Recall at k, Mean Reciprocal Rank, and nDCG.",
                page=1,
                section="Metrics",
                token_count=11,
                source_path="/tmp/evaluation_guidelines.txt",
            ),
        ]
        self.engine = RetrievalEngine(HashedEmbeddingModel())
        self.engine.update(self.chunks)

    def test_hybrid_retrieval_returns_relevant_chunk(self) -> None:
        question = "Which document mentions Recall at k, Mean Reciprocal Rank, and nDCG?"
        dense_hits = self.engine.dense_retrieve(question, top_k=5)
        keyword_hits = self.engine.keyword_retrieve(question, top_k=5)
        trace = self.engine.fuse_and_rerank(
            query=question,
            dense_hits=dense_hits,
            keyword_hits=keyword_hits,
            rerank_top_k=5,
            answer_top_k=3,
        )
        self.assertTrue(trace.reranked_hits)
        self.assertEqual(trace.reranked_hits[0].document_name, "evaluation_guidelines.txt")

    def test_heuristic_answer_and_verifier(self) -> None:
        answer = HeuristicChatModel().answer(
            "Why use hybrid retrieval?",
            [self.chunks[0]],
            "Not found in the provided documents.",
        )
        verification = OverlapVerifier().verify(answer, [self.chunks[0]])
        self.assertIn("Hybrid retrieval", answer)
        self.assertGreaterEqual(verification.support_score, 0.5)

    def test_ollama_chat_model_calls_local_chat_api(self) -> None:
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self) -> bytes:
                return b'{"message": {"content": "Hybrid retrieval combines dense retrieval and BM25."}}'

        captured = {}

        def fake_urlopen(request_obj, timeout):
            captured["url"] = request_obj.full_url
            captured["body"] = request_obj.data.decode("utf-8")
            captured["timeout"] = timeout
            return FakeResponse()

        with patch("app.services.models.request.urlopen", side_effect=fake_urlopen):
            answer = OllamaChatModel(
                base_url="http://localhost:11434",
                model="qwen2.5:0.5b",
                timeout_seconds=45,
            ).answer(
                "Why use hybrid retrieval?",
                [self.chunks[0]],
                "Not found in the provided documents.",
            )

        self.assertEqual(captured["url"], "http://localhost:11434/api/chat")
        self.assertIn('"model": "qwen2.5:0.5b"', captured["body"])
        self.assertEqual(captured["timeout"], 45)
        self.assertIn("Hybrid retrieval", answer)


if __name__ == "__main__":
    unittest.main()
