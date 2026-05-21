from sqlalchemy.orm import Session

from app.db.models import WidgetORM


class WidgetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_widget_id(self, widget_id: str) -> WidgetORM | None:
        return self.session.query(WidgetORM).filter(WidgetORM.widget_id == widget_id).one_or_none()

    def create(
        self,
        widget_id: str,
        allowed_origins: list[str],
        theme: dict,
        greeting: str,
        enabled_tools: list[str],
        created_by_user_id: int | None,
    ) -> WidgetORM:
        row = WidgetORM(
            widget_id=widget_id,
            allowed_origins=allowed_origins,
            theme=theme,
            greeting=greeting,
            enabled_tools=enabled_tools,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row