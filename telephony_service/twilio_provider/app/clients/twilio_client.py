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

from ..core.errors import TwilioAPIError


@dataclass(frozen=True)
class CallResult:
    sid: str
    status: str


class TwilioClient:
    def __init__(self, account_sid: str, auth_token: str, request_timeout: float = 10.0):
        self._client = Client(account_sid, auth_token, http_client=TwilioHttpClient(timeout=request_timeout))

    async def create_call(
        self, *, to: str, from_: str, twiml: str | None = None, url: str | None = None, timeout: int | None = None
    ) -> CallResult:
        if not twiml and not url:
            raise ValueError("Either twiml or url must be provided")
        # IMPORTANT: The Twilio SDK uses `values.unset` (a sentinel object) — NOT Python None —
        # to indicate "omit this field from the POST body". Passing None causes the SDK to
        # serialise it as an empty string, which Twilio rejects with "Required parameter missing".
        try:
            call = await asyncio.to_thread(
                self._client.calls.create,
                to=to,
                from_=from_,
                url=url if url else twilio_values.unset,
                twiml=twiml if twiml else twilio_values.unset,
                timeout=timeout if timeout is not None else twilio_values.unset,
            )
        except TwilioRestException as exc:
            raise TwilioAPIError(
                exc.msg or "Twilio rejected the request", http_status=exc.status, twilio_code=exc.code
            ) from exc
        except Exception as exc:  # network errors, timeouts, SDK bugs
            raise TwilioAPIError(f"could not reach Twilio ({type(exc).__name__})") from exc
        return CallResult(sid=call.sid, status=call.status)
