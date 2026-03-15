from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    jwt_secret: str
    access_token_expiry_minutes: int
    upload_dir: Path
    corpus_dir: Path
    benchmark_corpus_dir: Path
    benchmark_path: Path
    dense_top_k: int
    bm25_top_k: int
    rerank_top_k: int
    answer_top_k: int
    chunk_size: int
    chunk_overlap: int
    refusal_text: str
    model_provider: str = "local"
    gemini_api_key: str = ""
    gemini_api_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_generation_model: str = "gemini-2.5-flash-lite"
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_timeout_seconds: int = 30
    gemini_embedding_dimensions: int = 768
    max_upload_size_mb: int = 10

    def ensure_directories(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.corpus_dir.mkdir(parents=True, exist_ok=True)
        self.benchmark_corpus_dir.mkdir(parents=True, exist_ok=True)
        self.benchmark_path.parent.mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
    upload_dir = Path(os.getenv("UPLOAD_DIR", ROOT_DIR / "data" / "uploads"))
    corpus_dir = Path(os.getenv("CORPUS_DIR", ROOT_DIR / "data" / "corpus"))
    benchmark_corpus_dir = Path(
        os.getenv("BENCHMARK_CORPUS_DIR", ROOT_DIR / "data" / "benchmark_corpus")
    )
    benchmark_path = Path(
        os.getenv("BENCHMARK_PATH", ROOT_DIR / "data" / "evaluations" / "demo_benchmark.json")
    )

    return Settings(
        app_name=os.getenv("APP_NAME", "Reliable RAG Document Intelligence Platform"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        jwt_secret=os.getenv("JWT_SECRET", "change-me-before-production"),
        access_token_expiry_minutes=int(os.getenv("TOKEN_EXPIRY_MINUTES", "720")),
        upload_dir=upload_dir,
        corpus_dir=corpus_dir,
        benchmark_corpus_dir=benchmark_corpus_dir,
        benchmark_path=benchmark_path,
        dense_top_k=int(os.getenv("DENSE_TOP_K", "20")),
        bm25_top_k=int(os.getenv("BM25_TOP_K", "20")),
        rerank_top_k=int(os.getenv("RERANK_TOP_K", "20")),
        answer_top_k=int(os.getenv("ANSWER_TOP_K", "5")),
        chunk_size=int(os.getenv("CHUNK_SIZE", "650")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "125")),
        refusal_text=os.getenv("REFUSAL_TEXT", "Not found in the provided documents."),
        model_provider=os.getenv("MODEL_PROVIDER", "local"),
        gemini_api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
        gemini_api_base_url=os.getenv(
            "GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
        ),
        gemini_generation_model=os.getenv("GEMINI_GENERATION_MODEL", "gemini-2.5-flash-lite"),
        gemini_embedding_model=os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"),
        gemini_timeout_seconds=int(os.getenv("GEMINI_TIMEOUT_SECONDS", "30")),
        gemini_embedding_dimensions=int(os.getenv("GEMINI_EMBEDDING_DIMENSIONS", "768")),
        max_upload_size_mb=int(os.getenv("MAX_UPLOAD_SIZE_MB", "10")),
    )


settings = load_settings()
