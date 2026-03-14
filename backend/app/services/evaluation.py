from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from uuid import uuid4

from app.domain.types import BenchmarkSample, EvaluationRun, QueryResult, utc_now_iso


def load_benchmark(path: Path) -> list[BenchmarkSample]:
    raw_items = json.loads(path.read_text(encoding="utf-8"))
    return [
        BenchmarkSample(
            id=item["id"],
            question=item["question"],
            expected_document=item.get("expected_document", ""),
            expected_keywords=item.get("expected_keywords", []),
            negative=bool(item.get("negative", False)),
        )
        for item in raw_items
    ]


def recall_at_k(results: list[QueryResult], benchmark: list[BenchmarkSample]) -> float:
    hits = 0
    total = 0
    for sample, result in zip(benchmark, results):
        if sample.negative:
            continue
        total += 1
        retrieved_documents = {citation.document_name for citation in result.citations}
        if sample.expected_document in retrieved_documents:
            hits += 1
    return hits / total if total else 0.0


def reciprocal_rank(results: list[QueryResult], benchmark: list[BenchmarkSample]) -> float:
    scores: list[float] = []
    for sample, result in zip(benchmark, results):
        if sample.negative:
            continue
        rank = 0
        for index, citation in enumerate(result.citations, start=1):
            if citation.document_name == sample.expected_document:
                rank = index
                break
        scores.append(0.0 if rank == 0 else 1 / rank)
    return sum(scores) / len(scores) if scores else 0.0


def ndcg_at_k(results: list[QueryResult], benchmark: list[BenchmarkSample], k: int = 5) -> float:
    scores: list[float] = []
    for sample, result in zip(benchmark, results):
        if sample.negative:
            continue
        dcg = 0.0
        for index, citation in enumerate(result.citations[:k], start=1):
            relevance = 1.0 if citation.document_name == sample.expected_document else 0.0
            if relevance:
                dcg += relevance / math.log2(index + 1)
        ideal = 1.0
        scores.append(dcg / ideal if ideal else 0.0)
    return sum(scores) / len(scores) if scores else 0.0


def answer_keyword_accuracy(results: list[QueryResult], benchmark: list[BenchmarkSample]) -> float:
    scores: list[float] = []
    for sample, result in zip(benchmark, results):
        if sample.negative:
            continue
        answer_lower = result.answer.lower()
        if not sample.expected_keywords:
            scores.append(1.0)
            continue
        matched = sum(1 for keyword in sample.expected_keywords if keyword.lower() in answer_lower)
        scores.append(matched / len(sample.expected_keywords))
    return sum(scores) / len(scores) if scores else 0.0


def citation_accuracy(results: list[QueryResult], benchmark: list[BenchmarkSample]) -> float:
    scores: list[float] = []
    for sample, result in zip(benchmark, results):
        if sample.negative:
            continue
        if not result.citations:
            scores.append(0.0)
            continue
        scores.append(1.0 if result.citations[0].document_name == sample.expected_document else 0.0)
    return sum(scores) / len(scores) if scores else 0.0


def refusal_accuracy(results: list[QueryResult], benchmark: list[BenchmarkSample], refusal_text: str) -> float:
    scores: list[float] = []
    for sample, result in zip(benchmark, results):
        is_refusal = result.answer.strip() == refusal_text
        scores.append(1.0 if is_refusal == sample.negative else 0.0)
    return sum(scores) / len(scores) if scores else 0.0


def hallucination_rate(results: list[QueryResult]) -> float:
    total_sentences = 0
    hallucinated_sentences = 0
    for result in results:
        sentence_count = len([part for part in re.split(r"(?<=[.!?])\s+", result.answer) if part.strip()])
        unsupported = len(result.unsupported_sentences)
        total_sentences += max(sentence_count, 1)
        hallucinated_sentences += unsupported
    return hallucinated_sentences / total_sentences if total_sentences else 0.0


@dataclass(slots=True)
class EvaluationRunner:
    refusal_text: str

    def build_run(self, benchmark: list[BenchmarkSample], results: list[QueryResult]) -> EvaluationRun:
        return EvaluationRun(
            id=str(uuid4()),
            created_at=utc_now_iso(),
            sample_count=len(benchmark),
            retrieval_recall_at_5=round(recall_at_k(results, benchmark), 3),
            mrr=round(reciprocal_rank(results, benchmark), 3),
            ndcg_at_5=round(ndcg_at_k(results, benchmark), 3),
            answer_accuracy=round(answer_keyword_accuracy(results, benchmark), 3),
            citation_accuracy=round(citation_accuracy(results, benchmark), 3),
            refusal_accuracy=round(refusal_accuracy(results, benchmark, self.refusal_text), 3),
            hallucination_rate=round(hallucination_rate(results), 3),
            notes="Automated benchmark run using the current seeded corpus and pipeline configuration.",
        )
