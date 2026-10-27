"""Errors raised inside this provider, and their mapping to HTTP responses.

Routers can't register app-level exception handlers, so routes convert errors with
`to_http_exception` - this keeps the package self-contained.
"""
from fastapi import HTTPException

# Twilio error code -> actionable hint (the ones you will hit first).
_HINTS = {
    0:     "Twilio rejected an invalid or disallowed parameter. "
           "Verify your PUBLIC_BASE_URL and call parameters.",

    20003: "Authentication failed. Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.",
    21211: "The destination is not a valid phone number.",
    21212: "The configured 'from' number is not valid for this account.",
    21215: "Calling this country is not enabled. Enable it in Twilio Console > Voice > Geo permissions.",
    21219: "Trial account: the destination must be a verified number in the Twilio Console, "
           "or upgrade the account.",
}


class TwilioProviderError(Exception):
    """Base class for this package's errors."""


class InvalidCallRequest(TwilioProviderError):
    """The request is well-formed but not allowed (e.g. calling the caller ID itself)."""


class TwilioAPIError(TwilioProviderError):
    def __init__(self, message: str, *, http_status: int | None = None, twilio_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.http_status = http_status
        self.twilio_code = twilio_code

    @property
    def hint(self) -> str | None:
        return _HINTS.get(self.twilio_code) if self.twilio_code else None


def to_http_exception(exc: TwilioProviderError) -> HTTPException:
    if isinstance(exc, InvalidCallRequest):
        return HTTPException(status_code=422, detail={"error": "invalid_call_request", "message": str(exc)})

    assert isinstance(exc, TwilioAPIError)
    if exc.http_status in (400, 404):
        status = 422          # Twilio says our input is bad -> surface it to the caller
    elif exc.http_status == 429:
        status = 429
    else:
        status = 502          # auth/config problems, Twilio outage, network
    return HTTPException(
        status_code=status,
        detail={
            "error": "twilio_error",
            "twilio_code": exc.twilio_code,
            "message": exc.message,
            "hint": exc.hint,
        },
    )
