from __future__ import annotations

from app.core.security import create_access_token, decode_access_token, verify_password
from app.domain.types import UserAccount
from app.services.storage import AuditLogStore, UserStore


class AuthService:
    def __init__(self, user_store: UserStore, audit_store: AuditLogStore, secret: str, expiry_minutes: int) -> None:
        self.user_store = user_store
        self.audit_store = audit_store
        self.secret = secret
        self.expiry_minutes = expiry_minutes

    def authenticate(self, username: str, password: str) -> str:
        user = self.user_store.get(username)
        if not user or not verify_password(password, user.hashed_password):
            self.audit_store.append(actor=username, action="auth.login_failed", detail="Invalid credentials.")
            raise ValueError("Invalid username or password.")

        self.audit_store.append(actor=username, action="auth.login", detail="User logged in.")
        return create_access_token(username, self.secret, self.expiry_minutes)

    def get_user_from_token(self, token: str) -> UserAccount:
        payload = decode_access_token(token, self.secret)
        username = str(payload["sub"])
        user = self.user_store.get(username)
        if not user:
            raise ValueError("User not found for provided token.")
        return user

