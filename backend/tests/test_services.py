from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from app.domain.types import ChunkRecord
from app.services.chunking import ParsedPage, build_chunks
from app.services.models import HashedEmbeddingModel, HeuristicChatModel, OverlapVerifier
from app.services.parsing import parse_document
from app.services.retrieval import RetrievalEngine


class ParsingAndChunkingTests(unittest.TestCase):
    def test_parse_text_document(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "notes.txt"
            file_path.write_text("INTRODUCTION\nReliable RAG needs evidence and citations.", encoding="utf-8")
            parsed = parse_document(file_path)
            self.assertEqual(parsed.filename, "notes.txt")
            self.assertEqual(parsed.pages[0].section, "INTRODUCTION")

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


if __name__ == "__main__":
    unittest.main()
