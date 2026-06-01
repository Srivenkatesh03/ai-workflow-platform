from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.session import Session as UserSession
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def get_or_create_role(self, name: str = "operator", permissions: dict | None = None) -> Role:
        role = self.db.scalar(select(Role).where(Role.name == name))
        if role:
            return role

        role = Role(name=name, permissions=permissions or {"workflows": ["read", "create", "execute"]})
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def create_user(self, name: str, email: str, password_hash: str, role: Role) -> User:
        user = User(name=name, email=email.lower(), password_hash=password_hash, role_id=role.id)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user: User, name: str | None) -> User:
        if name is not None:
            user.name = name
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_session(self, user: User, refresh_token_hash: str, expires_at) -> UserSession:
        session = UserSession(user_id=user.id, refresh_token=refresh_token_hash, expires_at=expires_at)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_by_token_hash(self, refresh_token_hash: str) -> UserSession | None:
        return self.db.scalar(select(UserSession).where(UserSession.refresh_token == refresh_token_hash))

