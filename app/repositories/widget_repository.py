from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import WidgetORM


class WidgetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, row: WidgetORM) -> WidgetORM:
        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)
        return row

    def get_by_widget_id(self, widget_id: str) -> WidgetORM | None:
        statement = select(WidgetORM).where(
            WidgetORM.widget_id == widget_id
        )

        return self.session.scalar(statement)

    def update(self, row: WidgetORM) -> WidgetORM:
        self.session.flush()
        self.session.refresh(row)
        return row