from sqlalchemy import select
from app.core.config import settings
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.user import User


def main():
    with SessionLocal() as db:
        if db.scalar(select(User).limit(1)):
            return
        user = User(
            username=settings.initial_admin_username.strip().lower(),
            full_name=settings.initial_admin_name,
            password_hash=hash_password(settings.initial_admin_password),
            role="ADMIN",
            active=True,
        )
        db.add(user)
        db.commit()
        print(f"Initial admin created: {user.username}")


if __name__ == "__main__":
    main()
