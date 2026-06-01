from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, hash_token, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthTokens, AuthUser, LoginRequest, RefreshTokenRequest, RegisterRequest


class AuthService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)

    def register(self, payload: RegisterRequest) -> AuthTokens:
        existing_user = self.users.get_by_email(payload.email)
        if existing_user:
            raise HTTPException(status_code=409, detail="Email is already registered")

        role = self.users.get_or_create_role("operator")
        user = self.users.create_user(
            name=payload.name,
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=role,
        )
        return self._issue_tokens(user)

    def login(self, payload: LoginRequest) -> AuthTokens:
        user = self.users.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        return self._issue_tokens(user)

    def refresh(self, payload: RefreshTokenRequest) -> AuthTokens:
        session = self.users.get_session_by_token_hash(hash_token(payload.refresh_token))
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        user = self.users.get_by_id(session.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User no longer exists")
        return self._issue_tokens(user)

    def _issue_tokens(self, user: User) -> AuthTokens:
        role_name = user.role.name if user.role else "operator"
        access_token = create_access_token(str(user.id), {"email": user.email, "role": role_name})
        refresh_token = token_urlsafe(48)
        self.users.create_session(
            user=user,
            refresh_token_hash=hash_token(refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=14),
        )
        return AuthTokens(access_token=access_token, refresh_token=refresh_token, user=self._auth_user(user))

    def _auth_user(self, user: User) -> AuthUser:
        return AuthUser(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.name if user.role else "operator",
        )
