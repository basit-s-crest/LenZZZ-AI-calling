"""FastAPI dependencies – thin wrappers that pull pre-built objects from app.state.

Everything heavy (settings parsing, SDK client construction) happens exactly
once in `main.py`'s lifespan.  These functions just hand objects to route handlers.
"""
from fastapi import Depends, HTTPException, Request
from pydantic import ValidationError

from ..clients.twilio_client import TwilioClient
from ..config import AppSettings, TwilioSettings
from ..services.call_service import CallService


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def get_twilio_settings(request: Request) -> TwilioSettings:
    """Retrieve TwilioSettings from app.state (set in lifespan)."""
    return request.app.state.twilio_settings


def get_app_settings(request: Request) -> AppSettings:
    """Retrieve AppSettings from app.state (set in lifespan)."""
    return request.app.state.app_settings


# ---------------------------------------------------------------------------
# Clients & Services
# ---------------------------------------------------------------------------

def get_twilio_client(request: Request) -> TwilioClient:
    """Retrieve the shared TwilioClient from app.state."""
    return request.app.state.twilio_client


def get_call_service(request: Request) -> CallService:
    """Retrieve the shared CallService from app.state."""
    return request.app.state.call_service
