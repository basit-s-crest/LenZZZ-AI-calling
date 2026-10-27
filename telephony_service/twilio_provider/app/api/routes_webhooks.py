import logging

from fastapi import APIRouter, Depends, Request, Response

from twilio.twiml.voice_response import VoiceResponse

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
    twiml = build_stream_twiml(
        pipecat_ws_url=app_settings.pipecat_ws_url,
        connect_action_url=app_settings.connect_action_url,
        stream_status_url=app_settings.stream_status_url,
    )
    log.info("returning TwiML: %s", twiml)
    return Response(content=twiml, media_type="application/xml")


@router.post("/voice/connect-action")
async def connect_action(request: Request) -> Response:
    """Twilio hits this when <Connect> finishes or fails. Logs all diagnostic details."""
    form = await request.form()
    data = dict(form)
    log.warning("CONNECT ACTION CALLBACK from Twilio: %s", data)
    resp = VoiceResponse()
    resp.hangup()
    return Response(content=str(resp), media_type="application/xml")


@router.post("/voice/stream-status")
async def stream_status(request: Request) -> Response:
    """Twilio hits this when the media stream status updates (started, stopped, failed)."""
    form = await request.form()
    data = dict(form)
    log.info("STREAM STATUS CALLBACK from Twilio: %s", data)
    return Response(content="", media_type="text/plain")
