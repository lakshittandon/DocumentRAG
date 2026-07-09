from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from urllib import error, request
from typing import Protocol

from app.domain.types import ChunkRecord, SentenceSupport, VerificationResult
from app.services.text_utils import tokenize, tokenize_with_ngrams


class EmbeddingModel(Protocol):
    def embed(self, text: str, task_type: str | None = None, title: str | None = None) -> list[float]:
        raise NotImplementedError


class ChatModel(Protocol):
    def answer(self, question: str, contexts: list[ChunkRecord], refusal_text: str) -> str:
        raise NotImplementedError


class Verifier(Protocol):
    def verify(self, answer: str, evidence: list[ChunkRecord]) -> VerificationResult:
        raise NotImplementedError


@dataclass(slots=True)
class HashedEmbeddingModel:
    dimensions: int = 96

    def embed(self, text: str, task_type: str | None = None, title: str | None = None) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in tokenize_with_ngrams(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % self.dimensions
            sign = 1.0 if digest[2] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0.0:
            return vector
        return [value / norm for value in vector]


class GeminiAPIError(RuntimeError):
    pass


class OllamaAPIError(RuntimeError):
    pass


def _post_json(endpoint: str, payload: dict, timeout_seconds: int, headers: dict[str, str] | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    http_request = request.Request(
        endpoint,
        data=body,
        headers=request_headers,
        method="POST",
    )
    with request.urlopen(http_request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_gemini_json(
    *,
    api_base_url: str,
    api_key: str,
    path: str,
    payload: dict,
    timeout_seconds: int,
) -> dict:
    endpoint = f"{api_base_url.rstrip('/')}/{path.lstrip('/')}"
    body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise GeminiAPIError(f"Gemini API request failed with HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise GeminiAPIError(f"Gemini API request failed: {exc.reason}") from exc


def _extract_text(response_payload: dict) -> str:
    parts: list[str] = []
    for candidate in response_payload.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            text = part.get("text")
            if text:
                parts.append(text)
    return "\n".join(part.strip() for part in parts if part.strip()).strip()


@dataclass(slots=True)
class GeminiEmbeddingModel:
    api_key: str
    api_base_url: str
    model: str = "gemini-embedding-001"
    timeout_seconds: int = 30
    output_dimensionality: int = 768

    def embed(self, text: str, task_type: str | None = None, title: str | None = None) -> list[float]:
        payload: dict[str, object] = {
            "model": f"models/{self.model}",
            "content": {
                "parts": [
                    {
                        "text": text,
                    }
                ]
            },
        }
        if task_type:
            payload["taskType"] = task_type
        if title:
            payload["title"] = title
        if self.output_dimensionality > 0:
            payload["outputDimensionality"] = self.output_dimensionality

        response_payload = _post_gemini_json(
            api_base_url=self.api_base_url,
            api_key=self.api_key,
            path=f"models/{self.model}:embedContent",
            payload=payload,
            timeout_seconds=self.timeout_seconds,
        )

        embedding = response_payload.get("embedding", {})
        values = embedding.get("values")
        if not isinstance(values, list):
            raise GeminiAPIError("Gemini embedding response did not contain embedding values.")
        return [float(value) for value in values]


@dataclass(slots=True)
class GeminiChatModel:
    api_key: str
    api_base_url: str
    model: str = "gemini-3.1-flash-lite"
    timeout_seconds: int = 30
    temperature: float = 0.2

    def answer(self, question: str, contexts: list[ChunkRecord], refusal_text: str) -> str:
        if not contexts:
            return refusal_text

        evidence_lines = []
        for index, chunk in enumerate(contexts, start=1):
            evidence_lines.append(
                "\n".join(
                    [
                        f"[Evidence {index}]",
                        f"Document: {chunk.document_name}",
                        f"Page: {chunk.page}",
                        f"Section: {chunk.section}",
                        f"Text: {chunk.text}",
                    ]
                )
            )

        payload = {
            "system_instruction": {
                "parts": [
                    {
                        "text": (
                            "You are a grounded document QA assistant. "
                            "Use only the provided evidence. "
                            f"If the evidence is insufficient, reply with exactly: {refusal_text}"
                        )
                    }
                ]
            },
            "contents": [
                {
                    "parts": [
                        {
                            "text": "\n\n".join(
                                [
                                    f"Question: {question}",
                                    "Evidence:",
                                    *evidence_lines,
                                    (
                                        "Answer the question using only the evidence. "
                                        "Do not invent facts. Keep the answer concise."
                                    ),
                                ]
                            )
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": self.temperature,
            },
        }

        response_payload = _post_gemini_json(
            api_base_url=self.api_base_url,
            api_key=self.api_key,
            path=f"models/{self.model}:generateContent",
            payload=payload,
            timeout_seconds=self.timeout_seconds,
        )
        answer = _extract_text(response_payload)
        if not answer:
            return refusal_text
        if refusal_text.lower() in answer.strip().lower():
            return refusal_text
        return answer.strip()


@dataclass(slots=True)
class OllamaChatModel:
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:0.5b"
    timeout_seconds: int = 120
    temperature: float = 0.2
    api_key: str = ""

    def answer(self, question: str, contexts: list[ChunkRecord], refusal_text: str) -> str:
        if not contexts:
            return refusal_text

        evidence_lines = []
        for index, chunk in enumerate(contexts, start=1):
            evidence_lines.append(
                "\n".join(
                    [
                        f"[Evidence {index}]",
                        f"Document: {chunk.document_name}",
                        f"Page: {chunk.page}",
                        f"Section: {chunk.section}",
                        f"Text: {chunk.text}",
                    ]
                )
            )

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a grounded document QA assistant. "
                        "Use only the provided evidence. "
                        f"If the evidence is insufficient, reply with exactly: {refusal_text}"
                    ),
                },
                {
                    "role": "user",
                    "content": "\n\n".join(
                        [
                            f"Question: {question}",
                            "Evidence:",
                            *evidence_lines,
                            (
                                "Answer the question using only the evidence. "
                                "Do not invent facts. Keep the answer concise."
                            ),
                        ]
                    ),
                },
            ],
            "options": {"temperature": self.temperature},
        }

        base_url = self.base_url.rstrip("/")
        endpoint = f"{base_url}/chat" if base_url.endswith("/api") else f"{base_url}/api/chat"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
        try:
            response_payload = _post_json(endpoint, payload, self.timeout_seconds, headers=headers)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise OllamaAPIError(f"Ollama API request failed with HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise OllamaAPIError(f"Ollama API request failed: {exc.reason}") from exc

        message = response_payload.get("message", {})
        answer = str(message.get("content", "")).strip()
        if not answer:
            return refusal_text
        if refusal_text.lower() in answer.lower():
            return refusal_text
        return answer


@dataclass(slots=True)
class HeuristicChatModel:
    max_sentences: int = 3

    def answer(self, question: str, contexts: list[ChunkRecord], refusal_text: str) -> str:
        if not contexts:
            return refusal_text

        question_terms = set(tokenize(question))
        candidates: list[tuple[float, str]] = []

        for chunk in contexts:
            sentences = re.split(r"(?<=[.!?])\s+", chunk.text)
            for sentence in sentences:
                cleaned = sentence.strip()
                if not cleaned:
                    continue
                sentence_terms = set(tokenize(cleaned))
                if not sentence_terms:
                    continue
                overlap = len(question_terms & sentence_terms)
                lexical_density = overlap / max(len(question_terms), 1)
                if overlap == 0:
                    continue
                bonus = 0.1 if cleaned.lower().startswith(tuple(question_terms)) else 0.0
                candidates.append((lexical_density + bonus, cleaned))

        if not candidates:
            return refusal_text

        unique_sentences: list[str] = []
        seen = set()
        for _, sentence in sorted(candidates, key=lambda item: item[0], reverse=True):
            normalized = " ".join(sentence.lower().split())
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_sentences.append(sentence)
            if len(unique_sentences) >= self.max_sentences:
                break

        if not unique_sentences:
            return refusal_text

        return " ".join(unique_sentences)


@dataclass(slots=True)
class OverlapVerifier:
    minimum_overlap: int = 2

    def verify(self, answer: str, evidence: list[ChunkRecord]) -> VerificationResult:
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", answer) if part.strip()]
        if not sentences:
            return VerificationResult(support_score=0.0, unsupported_sentences=[])

        evidence_terms = [set(tokenize(chunk.text)) for chunk in evidence]
        sentence_support: list[SentenceSupport] = []

        for sentence in sentences:
            sentence_terms = set(tokenize(sentence))
            best_overlap = 0
            supporting_chunk_id: str | None = None
            for index, chunk_terms in enumerate(evidence_terms):
                overlap = len(sentence_terms & chunk_terms)
                if overlap > best_overlap:
                    best_overlap = overlap
                    supporting_chunk_id = evidence[index].id

            if best_overlap >= self.minimum_overlap:
                status = "supported"
                reason = "Sentence shares enough terms with retrieved evidence."
            elif best_overlap > 0:
                status = "partially_supported"
                reason = "Sentence has weak overlap with evidence and should be reviewed."
            else:
                status = "unsupported"
                reason = "No retrieved citation supports this claim."

            sentence_support.append(
                SentenceSupport(
                    sentence=sentence,
                    status=status,
                    best_overlap=best_overlap,
                    supporting_chunk_id=supporting_chunk_id,
                    reason=reason,
                )
            )

        unsupported = [item.sentence for item in sentence_support if item.status == "unsupported"]
        weighted_support = sum(
            1.0 if item.status == "supported" else 0.5 if item.status == "partially_supported" else 0.0
            for item in sentence_support
        )
        score = weighted_support / len(sentences)
        return VerificationResult(
            support_score=round(score, 3),
            unsupported_sentences=unsupported,
            sentence_support=sentence_support,
        )
