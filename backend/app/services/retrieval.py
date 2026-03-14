from __future__ import annotations

from collections import Counter, defaultdict
import math

from app.domain.types import ChunkRecord, QueryTrace, RetrievalHit
from app.services.models import EmbeddingModel
from app.services.text_utils import tokenize


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    return sum(a * b for a, b in zip(vector_a, vector_b))


class BM25Index:
    def __init__(self, chunks: list[ChunkRecord], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.chunks = chunks
        self.tokenized_chunks = [tokenize(chunk.text) for chunk in chunks]
        self.doc_freq: dict[str, int] = defaultdict(int)
        self.term_frequencies: list[Counter[str]] = []
        self.doc_lengths: list[int] = []

        for tokens in self.tokenized_chunks:
            counter = Counter(tokens)
            self.term_frequencies.append(counter)
            self.doc_lengths.append(len(tokens))
            for token in counter:
                self.doc_freq[token] += 1

        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0.0

    def score(self, query: str, top_k: int) -> list[RetrievalHit]:
        if not self.chunks:
            return []

        query_terms = tokenize(query)
        scores: list[tuple[float, ChunkRecord]] = []
        total_docs = len(self.chunks)

        for index, chunk in enumerate(self.chunks):
            counter = self.term_frequencies[index]
            doc_length = self.doc_lengths[index] or 1
            score = 0.0
            for term in query_terms:
                freq = counter.get(term, 0)
                if freq == 0:
                    continue
                doc_freq = self.doc_freq.get(term, 0)
                idf = math.log(1 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * doc_length / max(self.avg_doc_length, 1.0))
                score += idf * (numerator / denominator)
            if score > 0:
                scores.append((score, chunk))

        return [
            RetrievalHit(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_name=chunk.document_name,
                text=chunk.text,
                page=chunk.page,
                section=chunk.section,
                score=round(score, 4),
                source="bm25",
            )
            for score, chunk in sorted(scores, key=lambda item: item[0], reverse=True)[:top_k]
        ]


class RetrievalEngine:
    def __init__(self, embedder: EmbeddingModel) -> None:
        self.embedder = embedder
        self.chunks: list[ChunkRecord] = []
        self.chunk_vectors: dict[str, list[float]] = {}
        self.bm25 = BM25Index([])

    def update(self, chunks: list[ChunkRecord]) -> None:
        self.chunks = list(chunks)
        self.chunk_vectors = {
            chunk.id: self.embedder.embed(
                chunk.text,
                task_type="RETRIEVAL_DOCUMENT",
                title=chunk.document_name,
            )
            for chunk in self.chunks
        }
        self.bm25 = BM25Index(self.chunks)

    def dense_retrieve(self, query: str, top_k: int) -> list[RetrievalHit]:
        query_vector = self.embedder.embed(query, task_type="RETRIEVAL_QUERY")
        scores: list[tuple[float, ChunkRecord]] = []
        for chunk in self.chunks:
            vector = self.chunk_vectors.get(chunk.id, [])
            score = cosine_similarity(query_vector, vector) if vector else 0.0
            if score > 0:
                scores.append((score, chunk))

        return [
            RetrievalHit(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_name=chunk.document_name,
                text=chunk.text,
                page=chunk.page,
                section=chunk.section,
                score=round(score, 4),
                source="dense",
            )
            for score, chunk in sorted(scores, key=lambda item: item[0], reverse=True)[:top_k]
        ]

    def keyword_retrieve(self, query: str, top_k: int) -> list[RetrievalHit]:
        return self.bm25.score(query, top_k=top_k)

    def fuse_and_rerank(
        self,
        query: str,
        dense_hits: list[RetrievalHit],
        keyword_hits: list[RetrievalHit],
        rerank_top_k: int,
        answer_top_k: int,
    ) -> QueryTrace:
        combined: dict[str, RetrievalHit] = {}
        rrf_scores: defaultdict[str, float] = defaultdict(float)
        rank_constant = 60

        for ranked_hits in (dense_hits, keyword_hits):
            for rank, hit in enumerate(ranked_hits, start=1):
                rrf_scores[hit.chunk_id] += 1 / (rank_constant + rank)
                combined[hit.chunk_id] = hit

        fused_hits = []
        for chunk_id, score in sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True):
            base_hit = combined[chunk_id]
            fused_hits.append(
                RetrievalHit(
                    chunk_id=base_hit.chunk_id,
                    document_id=base_hit.document_id,
                    document_name=base_hit.document_name,
                    text=base_hit.text,
                    page=base_hit.page,
                    section=base_hit.section,
                    score=round(score, 4),
                    source="rrf",
                )
            )

        reranked = self._rerank(query, fused_hits[:rerank_top_k])[:answer_top_k]
        return QueryTrace(
            dense_hits=dense_hits,
            keyword_hits=keyword_hits,
            fused_hits=fused_hits[:rerank_top_k],
            reranked_hits=reranked,
        )

    def _rerank(self, query: str, hits: list[RetrievalHit]) -> list[RetrievalHit]:
        query_terms = set(tokenize(query))
        reranked: list[RetrievalHit] = []
        for hit in hits:
            hit_terms = set(tokenize(hit.text))
            lexical_overlap = len(query_terms & hit_terms)
            phrase_bonus = 0.15 if query.lower() in hit.text.lower() else 0.0
            score = hit.score + lexical_overlap + phrase_bonus
            reranked.append(
                RetrievalHit(
                    chunk_id=hit.chunk_id,
                    document_id=hit.document_id,
                    document_name=hit.document_name,
                    text=hit.text,
                    page=hit.page,
                    section=hit.section,
                    score=round(score, 4),
                    source="rerank",
                )
            )

        return sorted(reranked, key=lambda item: item.score, reverse=True)
