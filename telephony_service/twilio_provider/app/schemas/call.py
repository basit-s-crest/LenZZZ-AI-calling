from pydantic import BaseModel, Field, field_validator

from ..core.phone import is_e164


class CreateCallRequest(BaseModel):
    to_number: str = Field(description="Destination in E.164 format, e.g. +919876543210")
    from_number: str | None = Field(
        default=None, description="Caller ID (a number you own in Twilio). Defaults to TWILIO_FROM_NUMBER."
    )
    message: str | None = Field(
        default=None, min_length=1, max_length=500,
        description="Text spoken when the call is answered. Defaults to TWILIO_DEFAULT_MESSAGE.",
    )

    @field_validator("to_number", "from_number")
    @classmethod
    def _e164(cls, v: str | None) -> str | None:
        if v is not None and not is_e164(v):
            raise ValueError("must be E.164 format, e.g. +14155550100")
        return v


class CreateCallResponse(BaseModel):
    call_sid: str
    status: str            # Twilio's status right after creation, normally "queued"
    to_number: str
    from_number: str
