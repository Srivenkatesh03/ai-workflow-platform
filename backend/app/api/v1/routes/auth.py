from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.auth import AuthTokens, LoginRequest, RefreshTokenRequest, RegisterRequest
from app.schemas.common import APIResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=APIResponse[AuthTokens], status_code=201)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> APIResponse[AuthTokens]:
    return APIResponse(message="User registered", data=AuthService(db).register(payload))


@router.post("/login", response_model=APIResponse[AuthTokens])
async def login(payload: LoginRequest, db: Session = Depends(get_db)) -> APIResponse[AuthTokens]:
    return APIResponse(message="User authenticated", data=AuthService(db).login(payload))


@router.post("/refresh", response_model=APIResponse[AuthTokens])
async def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> APIResponse[AuthTokens]:
    return APIResponse(message="Token refreshed", data=AuthService(db).refresh(payload))
