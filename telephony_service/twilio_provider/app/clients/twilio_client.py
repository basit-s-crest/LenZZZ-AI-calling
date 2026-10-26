"""The ONLY module that talks to the Twilio SDK.

The SDK is blocking, so calls run in a worker thread to keep the event loop free.
SDK/network exceptions are converted to TwilioAPIError so nothing else imports Twilio types.
"""
import asyncio
from dataclasses import dataclass

from twilio.base.exceptions import TwilioRestException
from twilio.http.http_client import TwilioHttpClient
from twilio.rest import Client

from ..core.errors import TwilioAPIError


@dataclass(frozen=True)
class CallResult:
    sid: str
    status: str


class TwilioClient:
    def __init__(self, account_sid: str, auth_token: str, request_timeout: float = 10.0):
        self._client = Client(account_sid, auth_token, http_client=TwilioHttpClient(timeout=request_timeout))

    async def create_call(self, *, to: str, from_: str, twiml: str, timeout: int | None = None) -> CallResult:
        # `timeout` is restricted on trial accounts – only include it when explicitly set.
        kwargs: dict = {"to": to, "from_": from_, "twiml": twiml}
        if timeout is not None:
            kwargs["timeout"] = timeout
        try:
            call = await asyncio.to_thread(self._client.calls.create, **kwargs)
        except TwilioRestException as exc:
            raise TwilioAPIError(
                exc.msg or "Twilio rejected the request", http_status=exc.status, twilio_code=exc.code
            ) from exc
        except Exception as exc:  # network errors, timeouts, SDK bugs
            raise TwilioAPIError(f"could not reach Twilio ({type(exc).__name__})") from exc
        return CallResult(sid=call.sid, status=call.status)
