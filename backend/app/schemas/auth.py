from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not any(character.isupper() for character in value):
            raise ValueError("Password must contain at least one uppercase character")
        if not any(character.isdigit() for character in value):
            raise ValueError("Password must contain at least one number")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthUser(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: str


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    user: AuthUser


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class UserUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
