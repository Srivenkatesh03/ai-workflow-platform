from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthUser, UserUpdateRequest
from app.schemas.common import APIResponse

router = APIRouter()


def to_auth_user(user: User) -> AuthUser:
    return AuthUser(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role.name if user.role else "operator",
    )


@router.get("/me", response_model=APIResponse[AuthUser])
async def get_me(current_user: User = Depends(get_current_user)) -> APIResponse[AuthUser]:
    return APIResponse(data=to_auth_user(current_user))


@router.put("/me", response_model=APIResponse[AuthUser])
async def update_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponse[AuthUser]:
    user = UserRepository(db).update_user(current_user, payload.name)
    return APIResponse(message="User updated", data=to_auth_user(user))
