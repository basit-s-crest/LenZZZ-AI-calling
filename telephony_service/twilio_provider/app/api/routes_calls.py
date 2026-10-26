from fastapi import APIRouter, Depends

from ..core.errors import InvalidCallRequest, TwilioAPIError, to_http_exception
from ..schemas import CreateCallRequest, CreateCallResponse
from ..services.call_service import CallService
from .deps import get_call_service

router = APIRouter(prefix="/twilio", tags=["twilio"])


@router.post("/calls", response_model=CreateCallResponse, status_code=202)
async def create_call(
    body: CreateCallRequest,
    service: CallService = Depends(get_call_service),
) -> CreateCallResponse:
    """Place an outbound call. 202 = Twilio accepted it; the phone has not rung yet."""
    try:
        return await service.place_call(body)
    except (InvalidCallRequest, TwilioAPIError) as exc:
        raise to_http_exception(exc) from exc
