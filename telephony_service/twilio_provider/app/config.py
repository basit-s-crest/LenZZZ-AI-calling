"""Application settings, read from environment / .env.

Two models:
- TwilioSettings  (prefix TWILIO_) – Twilio account credentials & call defaults.
- AppSettings     (no prefix)       – Global app config (URLs, timeouts, etc.).

Both are constructed exactly once at startup and stored on `app.state`
(see main.py).  Any module that needs them receives them via FastAPI
Depends – no manual construction or lru_cache gymnastics required.
"""
import re

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_e164(v: str) -> bool:
    """Matches international format: + followed by 10 to 15 digits."""
    return bool(re.match(r"^\+[1-9]\d{1,14}$", v))


# ---------------------------------------------------------------------------
# Twilio-specific settings  (env vars prefixed with TWILIO_)
# ---------------------------------------------------------------------------

class TwilioSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TWILIO_", env_file=".env", extra="ignore")

    account_sid: str
    auth_token: SecretStr
    from_number: str                       # default caller ID (a number you own in Twilio)
    default_message: str = "Hello, this is a test call from our system."
    ring_timeout_seconds: int | None = None  # set TWILIO_RING_TIMEOUT_SECONDS in .env (not supported on trial accounts)
    #twiml_url: str | None = None             # set TWILIO_TWIML_URL to a TwiML Bin URL (recommended for trial accounts)

    @field_validator("account_sid")
    @classmethod
    def _sid(cls, v: str) -> str:
        if not v.startswith("AC"):
            raise ValueError("must start with 'AC'")
        return v

    @field_validator("from_number")
    @classmethod
    def _from(cls, v: str) -> str:
        if not is_e164(v):
            raise ValueError("must be E.164, e.g. +14155550100")
        return v


# ---------------------------------------------------------------------------
# Global app settings  (no prefix – plain env var names)
# ---------------------------------------------------------------------------

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    public_base_url: str
    status_callback_url: str | None = None   # Twilio POSTs status events here
    request_timeout: float = 10.0            # HTTP timeout for outbound Twilio SDK calls

    @property
    def voice_webhook_url(self) -> str:
        return f"{self.public_base_url.rstrip('/')}/twilio/voice/outbound"

    @property
    def pipecat_ws_url(self) -> str:
        return (
            self.public_base_url.rstrip("/")
            .replace("https://", "wss://", 1)
            .replace("http://", "ws://", 1)
            + "/ws"
        )

    @property
    def connect_action_url(self) -> str:
        return f"{self.public_base_url.rstrip('/')}/twilio/voice/connect-action"

    @property
    def stream_status_url(self) -> str:
        return f"{self.public_base_url.rstrip('/')}/twilio/voice/stream-status"

