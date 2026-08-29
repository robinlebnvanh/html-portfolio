"""Authentication dependencies for admin-only API actions."""

from __future__ import annotations

import hmac
import os
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.admin_auth import token_secret, verify_access_token


bearer_scheme = HTTPBearer(auto_error=False)


def require_admin_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> None:
    """Require the configured admin bearer token for write operations.

    The token is deliberately read from the environment so credentials never
    need to be committed to the repository. A missing configuration is an
    operational error; missing or invalid request credentials remain 401.
    """
    configured_token = os.getenv("ADMIN_API_TOKEN")

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not configured_token and not token_secret():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin authentication is not configured",
        )

    if configured_token and hmac.compare_digest(credentials.credentials, configured_token):
        return

    if verify_access_token(credentials.credentials):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid admin bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_admin_actor(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> str:
    """Return an auditable actor name while enforcing admin authentication."""

    require_admin_token(credentials)
    claims = verify_access_token(credentials.credentials)
    return str(claims["email"]) if claims else "api_token"
