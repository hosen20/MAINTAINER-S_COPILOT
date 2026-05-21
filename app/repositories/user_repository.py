from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import UserORM
from app.domain.auth import UserAuthRecord
from app.domain.users import UserRole


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def any_user_exists(self) -> bool:
        user = self.session.scalar(
            select(UserORM).limit(1)
        )
        return user is not None

    def get_by_email(self, email: str) -> UserAuthRecord | None:
        user = self.session.scalar(
            select(UserORM).where(UserORM.email == email.lower())
        )

        if user is None:
            return None

        return self._to_auth_record(user)

    def get_by_id(self, user_id: int) -> UserAuthRecord | None:
        user = self.session.get(UserORM, user_id)

        if user is None:
            return None

        return self._to_auth_record(user)

    def create_user(
        self,
        email: str,
        hashed_password: str,
        role: UserRole,
    ) -> UserAuthRecord:
        user = UserORM(
            email=email.lower(),
            hashed_password=hashed_password,
            role=role.value,
            is_active=True,
        )

        self.session.add(user)
        self.session.flush()
        self.session.refresh(user)

        return self._to_auth_record(user)

    def _to_auth_record(self, user: UserORM) -> UserAuthRecord:
        return UserAuthRecord(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            role=UserRole(user.role),
            is_active=user.is_active,
        )