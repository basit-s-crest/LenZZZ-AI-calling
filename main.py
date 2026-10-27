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
from fastapi.responses import FileResponse
from pydantic import SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from telephony_service.twilio_provider.app.api.routes_calls import router as twilio_router
from telephony_service.twilio_provider.app.api.routes_webhooks import router as twilio_webhook_router
from telephony_service.twilio_provider.app.clients.twilio_client import TwilioClient
from telephony_service.twilio_provider.app.config import AppSettings as TwilioAppSettings, TwilioSettings
from telephony_service.twilio_provider.app.services.call_service import CallService
from ai_agent.transports.browser_ws import router as voice_agent_router
from ai_agent.transports.twilio_ws import router as twilio_stream_router
from fastapi.staticfiles import StaticFiles

# from telnyx_provider import router as telnyx_router   # <- register later

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)

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
async def lifespan(app: FastAPI):
    if get_app_settings().service_api_key is None:
        log.warning("SERVICE_API_KEY is not set: API endpoints are unauthenticated (dev only)")

    # --- Twilio provider: build settings, client, service once at startup ---
    try:
        twilio_settings = TwilioSettings()
        twilio_app_settings = TwilioAppSettings()
    except ValidationError as exc:
        problems = [
            f"{'.'.join(map(str, e['loc'])).upper()}: {e['msg']}"
            for e in exc.errors()
        ]
        log.critical("Invalid Twilio configuration – fix these env vars: %s", problems)
        raise SystemExit(1) from exc

    twilio_client = TwilioClient(
        account_sid=twilio_settings.account_sid,
        auth_token=twilio_settings.auth_token.get_secret_value(),
        app_settings=twilio_app_settings,
    )
    call_service = CallService(
        client=twilio_client,
        settings=twilio_settings,
        app_settings=twilio_app_settings,
    )

    app.state.twilio_settings = twilio_settings
    app.state.app_settings = twilio_app_settings
    app.state.twilio_client = twilio_client
    app.state.call_service = call_service

    log.info(
        "Twilio provider ready  (account=%s, from=%s, pipecat_ws=%s)",
        twilio_settings.account_sid,
        twilio_settings.from_number,
        twilio_app_settings.pipecat_ws_url,
    )

    yield

    log.info("Telephony service shutting down")


app = FastAPI(title="Telephony & AI Voice Agent Service", lifespan=lifespan)


@app.get("/health", tags=["system"])
async def health() -> dict:
    return {"ok": True}


app.include_router(twilio_router, dependencies=[Depends(require_api_key)])
app.include_router(twilio_webhook_router)
# app.include_router(telnyx_router, dependencies=[Depends(require_api_key)])

# Twilio Media Streams WebSocket — receives call audio, runs STT→LLM→TTS pipeline
app.include_router(twilio_stream_router)

# Browser test UI WebSocket — for local mic testing without a real call
app.include_router(voice_agent_router)

# Mount static assets (JS, CSS, etc.) — explicit prefix, no catch-all
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
async def serve_ui() -> FileResponse:
    """Serves the browser test UI. Explicit route avoids catch-all that intercepts WebSocket upgrades."""
    return FileResponse("static/index.html")
