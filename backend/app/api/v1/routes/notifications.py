from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import APIResponse

router = APIRouter()


class NotificationRequest(BaseModel):
    recipient: EmailStr | str
    subject: str | None = None
    message: str


@router.post("/email", response_model=APIResponse[dict[str, str]])
async def send_email(
    payload: NotificationRequest, _: User = Depends(get_current_user)
) -> APIResponse[dict[str, str]]:
    return APIResponse(message="Email notification queued", data={"recipient": str(payload.recipient), "status": "queued"})


@router.post("/slack", response_model=APIResponse[dict[str, str]])
async def send_slack(
    payload: NotificationRequest, _: User = Depends(get_current_user)
) -> APIResponse[dict[str, str]]:
    return APIResponse(message="Slack notification queued", data={"recipient": str(payload.recipient), "status": "queued"})
