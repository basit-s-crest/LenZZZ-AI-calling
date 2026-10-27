import logging

from fastapi import APIRouter, Depends, Request, Response

from ..config import AppSettings
from ..services.twiml_builder import build_stream_twiml
from .deps import get_app_settings

log = logging.getLogger("twilio_provider")
router = APIRouter(prefix="/twilio", tags=["twilio-webhooks"])


@router.post("/voice/outbound")
async def outbound_voice(request: Request, app_settings: AppSettings = Depends(get_app_settings)) -> Response:
    """Twilio calls this when the customer answers. We reply with the stream TwiML."""
    form = await request.form()
    log.info("WEBHOOK HIT /voice/outbound CallSid=%s status=%s", form.get("CallSid"), form.get("CallStatus"))
    twiml = build_stream_twiml(app_settings.pipecat_ws_url)
    log.info("returning TwiML stream url=%s", app_settings.pipecat_ws_url)
    return Response(content=twiml, media_type="application/xml")