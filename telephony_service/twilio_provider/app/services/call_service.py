"""Business logic for placing a call. No HTTP and no Twilio SDK types in here."""
import logging

from ..clients.twilio_client import TwilioClient
from ..config import TwilioSettings
from ..core.errors import InvalidCallRequest
from ..core.phone import mask_number
from ..schemas import CreateCallRequest, CreateCallResponse
from .twiml_builder import build_say_twiml

log = logging.getLogger("twilio_provider")


class CallService:
    def __init__(self, client: TwilioClient, settings: TwilioSettings):
        self._client = client
        self._settings = settings

    async def place_call(self, req: CreateCallRequest) -> CreateCallResponse:
        from_number = req.from_number or self._settings.from_number
        if req.to_number == from_number:
            raise InvalidCallRequest("to_number and from_number must be different")

        twiml = build_say_twiml(req.message or self._settings.default_message)
        result = await self._client.create_call(
            to=req.to_number,
            from_=from_number,
            # Prefer a TwiML Bin URL (works on trial accounts); fall back to inline twiml.
            url=self._settings.twiml_url or None,
            twiml=None if self._settings.twiml_url else twiml,
            timeout=self._settings.ring_timeout_seconds,  # None omits it (required for trial accounts)
        )
        log.info("call created sid=%s to=%s status=%s", result.sid, mask_number(req.to_number), result.status)
        return CreateCallResponse(
            call_sid=result.sid, status=result.status, to_number=req.to_number, from_number=from_number
        )
