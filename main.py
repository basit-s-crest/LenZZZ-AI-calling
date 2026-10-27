"""Telephony service entry point.

Initialises the app and registers each provider's router. Providers are fully isolated
packages; this file is the only place that knows about all of them.

Run:  uvicorn main:app --reload --port 8080
"""
import hmac
import logging
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from telephony_service.twilio_provider.app.api.routes_calls import router as twilio_router
from ai_agent.transports.browser_ws import router as voice_agent_router
from fastapi.staticfiles import StaticFiles

# from telnyx_provider import router as telnyx_router   # <- register later

log = logging.getLogger("telephony")


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Shared secret the main project sends as `X-API-Key`. If unset, the API is OPEN (dev only).
    service_api_key: SecretStr | None = None


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = get_app_settings().service_api_key
    if expected is None:
        return
    if not x_api_key or not hmac.compare_digest(x_api_key, expected.get_secret_value()):
        raise HTTPException(status_code=401, detail="invalid or missing X-API-Key")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if get_app_settings().service_api_key is None:
        log.warning("SERVICE_API_KEY is not set: API endpoints are unauthenticated (dev only)")
    yield


app = FastAPI(title="Telephony & AI Voice Agent Service", lifespan=lifespan)


@app.get("/health", tags=["system"])
async def health() -> dict:
    return {"ok": True}


app.include_router(twilio_router, dependencies=[Depends(require_api_key)])
# app.include_router(telnyx_router, dependencies=[Depends(require_api_key)])

# Register AI Voice Agent WebSocket router
app.include_router(voice_agent_router)

# Mount static files for UI testing (http://localhost:8080)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/", StaticFiles(directory="static", html=True), name="ui")

