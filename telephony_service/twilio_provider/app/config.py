"""Twilio settings, read from environment / .env (prefix TWILIO_)."""
from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import re

# A robust E.164 validator helper if yours is causing issues
def is_e164(v: str) -> bool:
    # Matches international format: + followed by 10 to 15 digits
    return bool(re.match(r"^\+[1-9]\d{1,14}$", v))


class TwilioSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TWILIO_", env_file=".env", extra="ignore")

    account_sid: str
    auth_token: SecretStr
    from_number: str                       # default caller ID (a number you own in Twilio)
    default_message: str = "Hello, this is a test call from our system."
    ring_timeout_seconds: int | None = None  # set TWILIO_RING_TIMEOUT_SECONDS in .env (not supported on trial accounts)
    twiml_url: str | None = None             # set TWILIO_TWIML_URL to a TwiML Bin URL (recommended for trial accounts)

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


@lru_cache
def get_settings() -> TwilioSettings:
    return TwilioSettings()
