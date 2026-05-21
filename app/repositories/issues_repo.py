from sqlalchemy.orm import Session

from app.db.models import IssueORM
from app.domain.issues import IssueRecord


class IssuesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_many(self, issues: list[IssueRecord]) -> int:
        count = 0

        for issue in issues:
            existing = (
                self.session.query(IssueORM)
                .filter(IssueORM.repo == issue.repo, IssueORM.number == issue.number)
                .one_or_none()
            )

            values = issue.model_dump()
            values["mapped_label"] = issue.mapped_label.value if issue.mapped_label else None

            if existing:
                for key, value in values.items():
                    setattr(existing, key, value)
            else:
                self.session.add(IssueORM(**values))

            count += 1

        self.session.commit()
        return count