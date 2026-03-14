from __future__ import annotations

import re


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "does",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "to",
    "use",
    "used",
    "what",
    "when",
    "which",
    "why",
    "with",
}


def normalize_token(token: str) -> str:
    normalized = token.lower()
    for suffix in ("ations", "ation", "ments", "ment", "ingly", "ing", "ed", "es", "s"):
        if normalized.endswith(suffix) and len(normalized) > len(suffix) + 2:
            normalized = normalized[: -len(suffix)]
            break
    return normalized


def tokenize(text: str) -> list[str]:
    raw_tokens = re.findall(r"[A-Za-z0-9']+", text.lower())
    return [normalize_token(token) for token in raw_tokens if token not in STOPWORDS]


def tokenize_with_ngrams(text: str) -> list[str]:
    tokens = tokenize(text)
    ngrams: list[str] = []
    for token in tokens:
        if len(token) < 4:
            ngrams.append(token)
            continue
        ngrams.append(token)
        ngrams.extend(token[index : index + 3] for index in range(len(token) - 2))
    return ngrams
