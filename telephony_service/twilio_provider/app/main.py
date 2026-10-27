"""Application entry-point: FastAPI app factory with eager startup initialization.

Run with:  uvicorn twilio_provider.app.main:app --reload
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import ValidationError

from .api import calls_router, webhooks_router
from .clients.twilio_client import TwilioClient
from .config import AppSettings, TwilioSettings
from .services.call_service import CallService

log = logging.getLogger("twilio_provider")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eagerly build settings, SDK client, and services **once** at startup.

    If env vars are missing or invalid the process crashes immediately with a
    clear error – no silent 503s on the first request.
    """
    # --- 1.  Parse settings (fails fast on missing env vars) ---------------
    try:
        twilio_settings = TwilioSettings()
        app_settings = AppSettings()
    except ValidationError as exc:
        problems = [
            f"{'.'.join(map(str, e['loc'])).upper()}: {e['msg']}"
            for e in exc.errors()
        ]
        log.critical("Invalid configuration – fix these env vars: %s", problems)
        raise SystemExit(1) from exc

    # --- 2.  Build shared objects ------------------------------------------
    twilio_client = TwilioClient(
        account_sid=twilio_settings.account_sid,
        auth_token=twilio_settings.auth_token.get_secret_value(),
        app_settings=app_settings,
    )
    call_service = CallService(client=twilio_client, settings=twilio_settings, app_settings=app_settings)

    # --- 3.  Attach to app.state so deps.py can hand them out --------------
    app.state.twilio_settings = twilio_settings
    app.state.app_settings = app_settings
    app.state.twilio_client = twilio_client
    app.state.call_service = call_service

    log.info(
        "Twilio provider ready  (account=%s, from=%s, pipecat_ws=%s)",
        twilio_settings.account_sid,
        twilio_settings.from_number,
        app_settings.pipecat_ws_url,
    )

    yield  # ← app is running

    # --- Shutdown (add cleanup here if needed) -----------------------------
    log.info("Twilio provider shutting down")


def create_app() -> FastAPI:
    """Factory that wires everything together."""
    app = FastAPI(
        title="Twilio Provider",
        lifespan=lifespan,
    )
    app.include_router(calls_router)
    app.include_router(webhooks_router)
    return app


# Module-level instance for `uvicorn twilio_provider.app.main:app`
app = create_app()
