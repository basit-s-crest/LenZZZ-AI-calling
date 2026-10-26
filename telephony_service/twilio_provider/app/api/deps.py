from functools import lru_cache

from fastapi import HTTPException
from pydantic import ValidationError

from ..clients.twilio_client import TwilioClient
from ..config import get_settings
from ..services.call_service import CallService


@lru_cache
def _build_service() -> CallService:
    settings = get_settings()
    client = TwilioClient(settings.account_sid, settings.auth_token.get_secret_value())
    return CallService(client, settings)


def get_call_service() -> CallService:
    """FastAPI dependency. Missing/invalid config -> clear 503 naming the variables (never values)."""
    try:
        return _build_service()
    except ValidationError as exc:
        problems = [f"TWILIO_{'.'.join(map(str, e['loc'])).upper()}: {e['msg']}" for e in exc.errors()]
        raise HTTPException(
            status_code=503,
            detail={"error": "twilio_not_configured", "problems": problems},
        ) from None
