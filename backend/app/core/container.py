from __future__ import annotations

from app.core.config import settings
from app.services.auth import AuthService
from app.services.models import (
    GeminiChatModel,
    GeminiEmbeddingModel,
    HashedEmbeddingModel,
    HeuristicChatModel,
    OverlapVerifier,
)
from app.services.pipeline import RAGPipeline
from app.services.storage import AuditLogStore, KnowledgeBaseStore, UserStore


class AppContainer:
    def __init__(self) -> None:
        self.settings = settings
        self.user_store = UserStore()
        self.knowledge_base = KnowledgeBaseStore()
        self.audit_store = AuditLogStore()
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

        raise RuntimeError(
            f"Unsupported MODEL_PROVIDER '{self.settings.model_provider}'. Use 'local' or 'gemini'."
        )


container = AppContainer()
