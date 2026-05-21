from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.domain.auth import (
    AuthenticatedUser,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserAuthRecord,
)
from app.domain.errors import NotFoundError, PermissionDeniedError, ValidationError
from app.domain.users import UserRead, UserRole
from app.infra.settings import get_settings
from app.infra.vault import VaultClient
from app.repositories.user_repository import UserRepository


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

        settings = get_settings()
        self.secrets = VaultClient(settings).read_app_secrets()

    def register(self, payload: RegisterRequest) -> TokenResponse:
        existing_user = self.users.get_by_email(payload.email)

        if existing_user is not None:
            raise ValidationError("Email already exists.")

        role = (
            UserRole.user
            if self.users.any_user_exists()
            else UserRole.admin
        )

        user = self.users.create_user(
            email=payload.email,
            hashed_password=self.hash_password(payload.password),
            role=role,
        )

        self.session.commit()

        return self.build_token_response(user)

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.users.get_by_email(payload.email)

        if user is None:
            raise PermissionDeniedError("Invalid credentials.")

        if not user.is_active:
            raise PermissionDeniedError("User disabled.")

        if not self.verify_password(payload.password, user.hashed_password):
            raise PermissionDeniedError("Invalid credentials.")

        return self.build_token_response(user)

    def get_current_user(self, token: str) -> AuthenticatedUser:
        try:
            payload = jwt.decode(
                token,
                self.secrets.jwt_secret,
                algorithms=["HS256"],
            )
        except JWTError as exc:
            raise PermissionDeniedError("Invalid token.") from exc

        user_id = payload.get("sub")

        if user_id is None:
            raise PermissionDeniedError("Invalid token.")

        user = self.users.get_by_id(int(user_id))

        if user is None:
            raise NotFoundError("User not found.")

        if not user.is_active:
            raise PermissionDeniedError("User disabled.")

        return AuthenticatedUser(
            id=user.id,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
        )

    def require_admin(self, user: AuthenticatedUser) -> AuthenticatedUser:
        if user.role != UserRole.admin:
            raise PermissionDeniedError("Admin only.")

        return user

    def build_token_response(self, user: UserAuthRecord) -> TokenResponse:
        token = self.create_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value,
            }
        )

        return TokenResponse(
            access_token=token,
            user=UserRead(
                id=user.id,
                email=user.email,
                role=user.role,
                is_active=user.is_active,
            ),
        )

    def create_token(self, claims: dict[str, Any]) -> str:
        expiration = datetime.now(timezone.utc) + timedelta(hours=8)

        payload = {
            **claims,
            "exp": expiration,
        }

        return jwt.encode(
            payload,
            self.secrets.jwt_secret,
            algorithm="HS256",
        )

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)