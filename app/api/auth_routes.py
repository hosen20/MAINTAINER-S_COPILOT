from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.domain.auth import (
    AuthenticatedUser,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService


router = APIRouter()
bearer = HTTPBearer()


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer),
    ],
    session: Annotated[
        Session,
        Depends(get_session),
    ],
) -> AuthenticatedUser:
    return AuthService(session).get_current_user(
        credentials.credentials
    )


def require_admin(
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
    session: Annotated[
        Session,
        Depends(get_session),
    ],
) -> AuthenticatedUser:
    return AuthService(session).require_admin(current_user)


@router.post(
    "/register",
    response_model=TokenResponse,
)
def register(
    payload: RegisterRequest,
    session: Annotated[
        Session,
        Depends(get_session),
    ],
) -> TokenResponse:
    return AuthService(session).register(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: LoginRequest,
    session: Annotated[
        Session,
        Depends(get_session),
    ],
) -> TokenResponse:
    return AuthService(session).login(payload)


@router.get(
    "/me",
    response_model=AuthenticatedUser,
)
def me(
    current_user: Annotated[
        AuthenticatedUser,
        Depends(get_current_user),
    ],
) -> AuthenticatedUser:
    return current_user


@router.get(
    "/admin-check",
    response_model=AuthenticatedUser,
)
def admin_check(
    admin: Annotated[
        AuthenticatedUser,
        Depends(require_admin),
    ],
) -> AuthenticatedUser:
    return admin