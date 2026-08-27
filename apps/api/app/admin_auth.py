"""Admin user authentication and signed session tokens."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

from sqlalchemy import func, insert, select, update
from sqlalchemy.orm import Session

from app.sqlalchemy_tables import admin_users


HASH_ALGORITHM = "pbkdf2_sha256"
HASH_ITERATIONS = 210_000
TOKEN_TTL_SECONDS = 60 * 60 * 8


def normalize_email(email: str) -> str:
    """Return a stable lookup key for admin email addresses."""

    return email.strip().lower()


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2 so plaintext is never stored."""

    if not password:
        raise ValueError("password must not be blank")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        HASH_ITERATIONS,
    )
    return f"{HASH_ALGORITHM}${HASH_ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether a plaintext password matches the stored hash."""

    try:
        algorithm, iterations_text, salt_text, digest_text = password_hash.split("$", 3)
        if algorithm != HASH_ALGORITHM:
            return False
        expected = _b64decode(digest_text)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            _b64decode(salt_text),
            int(iterations_text),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def token_secret() -> str | None:
    """Return the configured signing secret for Admin Console sessions."""

    return os.getenv("ADMIN_AUTH_SECRET") or os.getenv("ADMIN_API_TOKEN")


def _sign(message: str, secret: str) -> str:
    signature = hmac.new(
        secret.encode("utf-8"),
        message.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64encode(signature)


def create_access_token(user: dict[str, Any], now: int | None = None) -> str:
    """Create a compact HMAC-signed admin access token."""

    secret = token_secret()
    if not secret:
        raise RuntimeError("admin token signing is not configured")

    issued_at = int(now or time.time())
    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "role": user["role"],
        "iat": issued_at,
        "exp": issued_at + TOKEN_TTL_SECONDS,
    }
    payload_text = _b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    return f"{payload_text}.{_sign(payload_text, secret)}"


def verify_access_token(token: str, now: int | None = None) -> dict[str, Any] | None:
    """Return verified token claims, or None for invalid/expired tokens."""

    secret = token_secret()
    if not secret or "." not in token:
        return None
    payload_text, signature = token.rsplit(".", 1)
    if not hmac.compare_digest(signature, _sign(payload_text, secret)):
        return None
    try:
        payload = json.loads(_b64decode(payload_text).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    if int(payload.get("exp", 0)) < int(now or time.time()):
        return None
    if payload.get("role") != "admin":
        return None
    return payload


def row_to_admin_user(row: dict[str, Any]) -> dict[str, Any]:
    """Return the public admin user shape."""

    return {
        "id": row["id"],
        "email": row["email"],
        "role": row["role"],
    }


def get_admin_user_by_email(session: Session, email: str) -> dict[str, Any] | None:
    """Load an admin user including password hash for authentication."""

    row = session.execute(
        select(
            admin_users.c.id,
            admin_users.c.email,
            admin_users.c.password_hash,
            admin_users.c.role,
        ).where(admin_users.c.email == normalize_email(email))
    ).mappings().first()
    return dict(row) if row else None


def create_admin_user(session: Session, email: str, password: str) -> dict[str, Any]:
    """Create one admin user and return the public shape."""

    result = session.execute(
        insert(admin_users).values(
            email=normalize_email(email),
            password_hash=hash_password(password),
            role="admin",
        )
    )
    session.commit()
    user_id = result.inserted_primary_key[0]
    row = session.execute(
        select(admin_users.c.id, admin_users.c.email, admin_users.c.role).where(
            admin_users.c.id == user_id
        )
    ).mappings().one()
    return row_to_admin_user(dict(row))


def ensure_bootstrap_admin_user(session: Session) -> None:
    """Create the first admin user from environment variables when needed."""

    existing_count = session.scalar(select(func.count()).select_from(admin_users))
    if existing_count:
        return

    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    if not email or not password:
        return

    create_admin_user(session, email, password)


def authenticate_admin_user(
    session: Session,
    email: str,
    password: str,
) -> dict[str, Any] | None:
    """Validate email/password and return the public user shape."""

    user = get_admin_user_by_email(session, email)
    if not user or not verify_password(password, user["password_hash"]):
        return None

    session.execute(
        update(admin_users)
        .where(admin_users.c.id == user["id"])
        .values(last_login_at=func.current_timestamp())
    )
    session.commit()
    return row_to_admin_user(user)
