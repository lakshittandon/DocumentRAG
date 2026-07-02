from __future__ import annotations

from pathlib import Path
import shutil
import time

from fastapi import APIRouter, Depends, File, HTTPException, Security, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.container import container
from app.domain.types import UserAccount
from app.schemas.api import (
    AuditLogResponse,
    ConflictAnalysisResponse,
    DeleteDocumentResponse,
    DocumentResponse,
    EvaluationRunResponse,
    HealthResponse,
    LoginRequest,
    QueryRequest,
    QueryResponse,
    ReindexResponse,
    TokenResponse,
    UpdateDocumentPermissionsRequest,
    VersionComparisonResponse,
)
from app.services.parsing import UnsupportedDocumentError


router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def get_container():
    return container


def _map_document(document) -> DocumentResponse:
    return DocumentResponse(**document.to_dict())


def _map_query(result) -> QueryResponse:
    return QueryResponse(**result.to_dict())

def _map_log(entry) -> AuditLogResponse:
    return AuditLogResponse(**entry.to_dict())


def _map_evaluation(run) -> EvaluationRunResponse:
    return EvaluationRunResponse(**run.to_dict())


def _map_version_comparison(comparison) -> VersionComparisonResponse:
    return VersionComparisonResponse(**comparison.to_dict())


def _map_conflict_analysis(analysis) -> ConflictAnalysisResponse:
    return ConflictAnalysisResponse(**analysis.to_dict())


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    app_container=Depends(get_container),
) -> UserAccount:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    try:
        return app_container.auth_service.get_user_from_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, app_container=Depends(get_container)) -> TokenResponse:
    try:
        token = app_container.auth_service.authenticate(payload.username, payload.password)
        user = app_container.user_store.get(payload.username)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return TokenResponse(access_token=token, username=user.username, role=user.role)


@router.get("/health", response_model=HealthResponse)
def health(app_container=Depends(get_container)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=app_container.settings.app_version,
        documents_indexed=len(app_container.pipeline.list_documents()),
        model_provider=app_container.settings.model_provider,
        generation_model=(
            app_container.settings.gemini_generation_model
            if app_container.settings.model_provider == "gemini"
            else "local-heuristic"
        ),
        embedding_model=(
            app_container.settings.gemini_embedding_model
            if app_container.settings.model_provider == "gemini"
            else "local-hashed"
        ),
        max_upload_size_mb=app_container.settings.max_upload_size_mb,
        storage_backend="postgresql" if app_container.settings.database_url else "memory",
        ocr_enabled=app_container.settings.enable_ocr,
    )


@router.get("/documents", response_model=list[DocumentResponse])
def list_documents(
    current_user: UserAccount = Depends(get_current_user),
    app_container=Depends(get_container),
) -> list[DocumentResponse]:
    return [
        _map_document(document)
        for document in app_container.pipeline.list_documents(
            actor=current_user.username,
            role=current_user.role,
        )
    ]


@router.post("/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserAccount = Depends(get_current_user),
    app_container=Depends(get_container),
) -> DocumentResponse:
    filename = Path(file.filename or "upload.txt").name
    timestamp = int(time.time())
    destination = app_container.settings.upload_dir / f"{timestamp}_{filename}"
    max_upload_bytes = app_container.settings.max_upload_size_mb * 1024 * 1024

    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = destination.stat().st_size
    if file_size > max_upload_bytes:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File exceeds the {app_container.settings.max_upload_size_mb} MB upload limit. "
                f"Please upload a smaller file or split the PDF."
            ),
        )

    try:
        document = app_container.pipeline.queue_ingest_file(
            destination,
            actor=current_user.username,
            content_type=file.content_type or "application/octet-stream",
        )
        return _map_document(document)
    except UnsupportedDocumentError as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/documents/{document_id}/reindex", response_model=ReindexResponse)
def reindex_document(
    document_id: str,
    current_user: UserAccount = Depends(get_current_user),
    app_container=Depends(get_container),
) -> ReindexResponse:
    try:
        document = app_container.pipeline.reindex_document(document_id, actor=current_user.username)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ReindexResponse(message="Document reindexed successfully.", document=_map_document(document))


@router.delete("/documents/{document_id}", response_model=DeleteDocumentResponse)
def delete_document(
    document_id: str,
    current_user: UserAccount = Depends(get_current_user),
    app_container=Depends(get_container),
) -> DeleteDocumentResponse:
    try:
        document = app_container.pipeline.delete_document(document_id, actor=current_user.username)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return DeleteDocumentResponse(
        message=f"Deleted {document.filename} successfully.",
        document_id=document.id,
    )


@router.patch("/documents/{document_id}/permissions", response_model=DocumentResponse)
def update_document_permissions(
    document_id: str,
    payload: UpdateDocumentPermissionsRequest,
    current_user: UserAccount = Depends(get_current_user),
    app_container=Depends(get_container),
) -> DocumentResponse:
    try:
        document = app_container.pipeline.update_document_permissions(
            document_id=document_id,
            actor=current_user.username,
            role=current_user.role,
            visibility=payload.visibility,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _map_document(document)


@router.get("/documents/{document_id}/versions", response_model=list[DocumentResponse])
def list_document_versions(
    document_id: str,
    current_user: UserAccount = Depends(get_current_user),
    app_container=Depends(get_container),
) -> list[DocumentResponse]:
    try:
        versions = app_container.pipeline.list_document_versions(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [_map_document(document) for document in versions]


@router.post(
    "/documents/{base_document_id}/compare/{target_document_id}",
    response_model=VersionComparisonResponse,
)
def compare_document_versions(
    base_document_id: str,
    target_document_id: str,
    current_user: UserAccount = Depends(get_current_user),
    app_container=Depends(get_container),
) -> VersionComparisonResponse:
    try:
        comparison = app_container.pipeline.compare_document_versions(
            base_document_id=base_document_id,
            target_document_id=target_document_id,
            actor=current_user.username,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _map_version_comparison(comparison)


@router.post("/query", response_model=QueryResponse)
def run_query(
    payload: QueryRequest,
    current_user: UserAccount = Depends(get_current_user),
    app_container=Depends(get_container),
) -> QueryResponse:
    result = app_container.pipeline.query(
        payload.question,
        actor=current_user.username,
        role=current_user.role,
    )
    return _map_query(result)


@router.get("/logs", response_model=list[AuditLogResponse])
def list_logs(
    current_user: UserAccount = Depends(get_current_user),
    app_container=Depends(get_container),
) -> list[AuditLogResponse]:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return [_map_log(entry) for entry in app_container.pipeline.list_logs()]


@router.post("/evaluations/run", response_model=EvaluationRunResponse)
def run_evaluation(
    current_user: UserAccount = Depends(get_current_user),
    app_container=Depends(get_container),
) -> EvaluationRunResponse:
    run = app_container.pipeline.run_evaluation(actor=current_user.username)
    return _map_evaluation(run)


@router.get("/evaluations", response_model=list[EvaluationRunResponse])
def list_evaluations(
    current_user: UserAccount = Depends(get_current_user),
    app_container=Depends(get_container),
) -> list[EvaluationRunResponse]:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return [_map_evaluation(run) for run in app_container.pipeline.list_evaluation_runs()]


@router.post("/analysis/conflicts", response_model=ConflictAnalysisResponse)
def analyze_conflicts(
    current_user: UserAccount = Depends(get_current_user),
    app_container=Depends(get_container),
) -> ConflictAnalysisResponse:
    analysis = app_container.pipeline.analyze_conflicts(actor=current_user.username)
    return _map_conflict_analysis(analysis)
