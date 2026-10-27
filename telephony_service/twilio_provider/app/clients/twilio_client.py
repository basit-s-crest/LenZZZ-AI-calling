"""The ONLY module that talks to the Twilio SDK.

The SDK is blocking, so calls run in a worker thread to keep the event loop free.
SDK/network exceptions are converted to TwilioAPIError so nothing else imports Twilio types.
"""
import asyncio
from dataclasses import dataclass

from twilio.base import values as twilio_values
from twilio.base.exceptions import TwilioRestException
from twilio.http.http_client import TwilioHttpClient
from twilio.rest import Client

from ..config import AppSettings
from ..core.errors import TwilioAPIError
from ..services.twiml_builder import build_stream_twiml


@dataclass(frozen=True)
class CallResult:
    sid: str
    status: str


class TwilioClient:
    def __init__(self, account_sid: str, auth_token: str, app_settings: AppSettings):
        self._client = Client(
            account_sid,
            auth_token,
            http_client=TwilioHttpClient(timeout=app_settings.request_timeout),
        )
        self._app_settings = app_settings

    async def create_call(
        self, *, to: str, from_: str, url: str
    ) -> CallResult:

        status_callback = self._app_settings.status_callback_url
        try:
            call = await asyncio.to_thread(
                self._client.calls.create,
                to=to,
                from_=from_,
                url=url,
                # method="POST",
                # status_callback=status_callback if status_callback else twilio_values.unset,
                # status_callback_event=["initiated", "ringing", "answered", "completed"] if status_callback else twilio_values.unset,
            )
        except TwilioRestException as exc:
            raise TwilioAPIError(
                exc.msg or "Twilio rejected the request", http_status=exc.status, twilio_code=exc.code
            ) from exc
        except Exception as exc:  # network errors, timeouts, SDK bugs
            raise TwilioAPIError(f"could not reach Twilio ({type(exc).__name__})") from exc
        return CallResult(sid=call.sid, status=call.status)
