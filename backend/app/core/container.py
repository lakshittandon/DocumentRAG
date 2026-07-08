from __future__ import annotations

from app.core.config import settings
from app.services.auth import AuthService
from app.services.models import (
    GeminiChatModel,
    GeminiEmbeddingModel,
    HashedEmbeddingModel,
    HeuristicChatModel,
    OllamaChatModel,
    OverlapVerifier,
)
from app.services.pipeline import RAGPipeline
from app.services.storage import (
    AuditLogStore,
    KnowledgeBaseStore,
    PostgresAuditLogStore,
    PostgresKnowledgeBaseStore,
    PostgresUserStore,
    UserStore,
)


class AppContainer:
    def __init__(self) -> None:
        self.settings = settings
        self.knowledge_base, self.audit_store, self.user_store = self._build_stores()
        self.auth_service = AuthService(
            user_store=self.user_store,
            audit_store=self.audit_store,
            secret=self.settings.jwt_secret,
            expiry_minutes=self.settings.access_token_expiry_minutes,
        )
        embedder, chat_model, verifier = self._build_model_stack()
        self.pipeline = RAGPipeline(
            settings=self.settings,
            store=self.knowledge_base,
            audit_store=self.audit_store,
            embedder=embedder,
            chat_model=chat_model,
            verifier=verifier,
        )

    def startup(self) -> None:
        self.pipeline.bootstrap()

    def available_query_providers(self) -> list[str]:
        providers: list[str] = []
        if self.settings.gemini_api_key:
            providers.append("gemini")

        if self.settings.ollama_base_url and (
            not self._uses_ollama_cloud() or bool(self.settings.ollama_api_key)
        ):
            providers.append("ollama")

        return providers

    def get_query_chat_model(self, provider: str):
        normalized_provider = provider.strip().lower()
        if normalized_provider == "gemini":
            if not self.settings.gemini_api_key:
                raise ValueError("Gemini is not configured. Add GEMINI_API_KEY to use Gemini answers.")
            return (
                GeminiChatModel(
                    api_key=self.settings.gemini_api_key,
                    api_base_url=self.settings.gemini_api_base_url,
                    model=self.settings.gemini_generation_model,
                    timeout_seconds=self.settings.gemini_timeout_seconds,
                ),
                "gemini",
                self.settings.gemini_generation_model,
            )

        if normalized_provider == "ollama":
            if self._uses_ollama_cloud() and not self.settings.ollama_api_key:
                raise ValueError("Ollama Cloud is not configured. Add OLLAMA_API_KEY to use Ollama/Qwen answers.")
            return (
                OllamaChatModel(
                    base_url=self.settings.ollama_base_url,
                    model=self.settings.ollama_model,
                    timeout_seconds=self.settings.ollama_timeout_seconds,
                    api_key=self.settings.ollama_api_key,
                ),
                "ollama",
                self.settings.ollama_model,
            )

        raise ValueError("Unsupported model provider. Choose 'gemini' or 'ollama'.")

    def _build_model_stack(self):
        if self.settings.model_provider == "local":
            return HashedEmbeddingModel(), HeuristicChatModel(), OverlapVerifier()

        if self.settings.model_provider == "gemini":
            if not self.settings.gemini_api_key:
                raise RuntimeError(
                    "MODEL_PROVIDER is set to 'gemini' but GEMINI_API_KEY is missing."
                )
            return (
                GeminiEmbeddingModel(
                    api_key=self.settings.gemini_api_key,
                    api_base_url=self.settings.gemini_api_base_url,
                    model=self.settings.gemini_embedding_model,
                    timeout_seconds=self.settings.gemini_timeout_seconds,
                    output_dimensionality=self.settings.gemini_embedding_dimensions,
                ),
                GeminiChatModel(
                    api_key=self.settings.gemini_api_key,
                    api_base_url=self.settings.gemini_api_base_url,
                    model=self.settings.gemini_generation_model,
                    timeout_seconds=self.settings.gemini_timeout_seconds,
                ),
                OverlapVerifier(),
            )

        if self.settings.model_provider == "ollama":
            return (
                HashedEmbeddingModel(),
                OllamaChatModel(
                    base_url=self.settings.ollama_base_url,
                    model=self.settings.ollama_model,
                    timeout_seconds=self.settings.ollama_timeout_seconds,
                    api_key=self.settings.ollama_api_key,
                ),
                OverlapVerifier(),
            )

        raise RuntimeError(
            f"Unsupported MODEL_PROVIDER '{self.settings.model_provider}'. Use 'local', 'gemini', or 'ollama'."
        )

    def _build_stores(self):
        if self.settings.database_url:
            return (
                PostgresKnowledgeBaseStore(self.settings.database_url),
                PostgresAuditLogStore(self.settings.database_url),
                PostgresUserStore(self.settings.database_url),
            )
        return KnowledgeBaseStore(), AuditLogStore(), UserStore()

    def _uses_ollama_cloud(self) -> bool:
        return self.settings.ollama_base_url.rstrip("/").lower().startswith("https://ollama.com")


container = AppContainer()
