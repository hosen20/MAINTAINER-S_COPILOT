from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import WidgetORM
from app.domain.auth import AuthenticatedUser
from app.domain.errors import NotFoundError, PermissionDeniedError
from app.domain.widget import (
    PublicWidgetConfig,
    WidgetConfigCreate,
    WidgetConfigRead,
    WidgetConfigUpdate,
)
from app.infra.redaction import redact_value
from app.repositories.audit_repo import AuditRepository
from app.repositories.widget_repository import WidgetRepository


class WidgetService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.widgets = WidgetRepository(session)
        self.audit = AuditRepository(session)

    def create(
        self,
        *,
        actor: AuthenticatedUser,
        payload: WidgetConfigCreate,
    ) -> WidgetConfigRead:
        self._require_admin(actor)

        row = WidgetORM(
            widget_id=uuid4().hex,
            allowed_origins=payload.allowed_origins,
            theme=payload.theme,
            greeting=payload.greeting,
            enabled_tools=payload.enabled_tools,
            is_active=True,
            created_by_user_id=actor.id,
        )

        row = self.widgets.create(row)

        self.audit.write(
            actor_user_id=actor.id,
            action="widget.create",
            target=f"widget:{row.widget_id}",
            metadata=redact_value(
                {
                    "allowed_origins": payload.allowed_origins,
                    "enabled_tools": payload.enabled_tools,
                }
            ),
        )

        self.session.commit()

        return WidgetConfigRead.model_validate(row)

    def update(
        self,
        *,
        actor: AuthenticatedUser,
        widget_id: str,
        payload: WidgetConfigUpdate,
    ) -> WidgetConfigRead:
        self._require_admin(actor)

        row = self.widgets.get_by_widget_id(widget_id)

        if row is None:
            raise NotFoundError("Widget not found.")

        if payload.allowed_origins is not None:
            row.allowed_origins = payload.allowed_origins

        if payload.theme is not None:
            row.theme = payload.theme

        if payload.greeting is not None:
            row.greeting = payload.greeting

        if payload.enabled_tools is not None:
            row.enabled_tools = payload.enabled_tools

        if payload.is_active is not None:
            row.is_active = payload.is_active

        row = self.widgets.update(row)

        self.audit.write(
            actor_user_id=actor.id,
            action="widget.update",
            target=f"widget:{row.widget_id}",
            metadata=redact_value(payload.model_dump(exclude_none=True)),
        )

        self.session.commit()

        return WidgetConfigRead.model_validate(row)

    def get_admin(
        self,
        *,
        actor: AuthenticatedUser,
        widget_id: str,
    ) -> WidgetConfigRead:
        self._require_admin(actor)

        row = self.widgets.get_by_widget_id(widget_id)

        if row is None:
            raise NotFoundError("Widget not found.")

        return WidgetConfigRead.model_validate(row)

    def get_public(self, widget_id: str) -> PublicWidgetConfig:
        row = self.widgets.get_by_widget_id(widget_id)

        if row is None or not row.is_active:
            raise NotFoundError("Widget not found.")

        return PublicWidgetConfig(
            widget_id=row.widget_id,
            theme=row.theme,
            greeting=row.greeting,
            enabled_tools=row.enabled_tools,
        )

    def get_allowed_origins(self, widget_id: str) -> list[str]:
        row = self.widgets.get_by_widget_id(widget_id)

        if row is None or not row.is_active:
            raise NotFoundError("Widget not found.")

        return row.allowed_origins

    def _require_admin(self, actor: AuthenticatedUser) -> None:
        if actor.role.value != "admin":
            raise PermissionDeniedError("Admin required.")