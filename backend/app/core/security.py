from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any


def _urlsafe_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _urlsafe_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str, salt: str | None = None) -> str:
    salt_value = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_value.encode("utf-8"),
        100_000,
    ).hex()
    return f"{salt_value}${digest}"


def verify_password(password: str, hashed_password: str) -> bool:
    salt, expected_digest = hashed_password.split("$", 1)
    actual_digest = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(actual_digest, expected_digest)


def create_access_token(subject: str, secret: str, expires_minutes: int) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": subject, "exp": int(time.time()) + expires_minutes * 60}

    header_part = _urlsafe_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _urlsafe_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    message = f"{header_part}.{payload_part}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return f"{header_part}.{payload_part}.{_urlsafe_encode(signature)}"


def decode_access_token(token: str, secret: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature_part = token.split(".")
    except ValueError as exc:
        raise ValueError("Invalid token format.") from exc

    message = f"{header_part}.{payload_part}".encode("utf-8")
    expected_signature = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    actual_signature = _urlsafe_decode(signature_part)

    if not hmac.compare_digest(expected_signature, actual_signature):
        raise ValueError("Invalid token signature.")

    payload = json.loads(_urlsafe_decode(payload_part).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("Token has expired.")

    return payload

