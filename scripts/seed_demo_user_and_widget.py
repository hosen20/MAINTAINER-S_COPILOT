from passlib.context import CryptContext

from app.db.models import UserORM, WidgetORM
from app.db.session import SessionLocal


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def main() -> None:
    session = SessionLocal()

    try:
        admin = (
            session.query(UserORM)
            .filter(UserORM.email == "admin@example.com")
            .one_or_none()
        )

        if admin is None:
            admin = UserORM(
                email="admin@example.com",
                hashed_password=pwd_context.hash("Password123!"),
                role="admin",
                is_active=True,
            )

            session.add(admin)
            session.flush()
            session.refresh(admin)

            print("Created demo admin: admin@example.com / Password123!")
        else:
            print("Demo admin already exists.")

        widget = (
            session.query(WidgetORM)
            .filter(WidgetORM.widget_id == "demo")
            .one_or_none()
        )

        if widget is None:
            widget = WidgetORM(
                widget_id="demo",
                allowed_origins=[
                    "http://localhost:8080",
                    "http://localhost:5173",
                    "http://localhost:8000",
                ],
                theme={
                    "primary_color": "#2563eb",
                    "position": "bottom-right",
                },
                greeting="Hi 👋 I am Maintainer's Copilot. Ask me about issues, docs, or triage.",
                enabled_tools=[
                    "classifier",
                    "ner",
                    "summarizer",
                    "rag",
                    "write_memory",
                ],
                is_active=True,
                created_by_user_id=admin.id,
            )

            session.add(widget)
            print("Created demo widget with widget_id='demo'.")
        else:
            print("Demo widget already exists.")

        session.commit()

    finally:
        session.close()


if __name__ == "__main__":
    main()