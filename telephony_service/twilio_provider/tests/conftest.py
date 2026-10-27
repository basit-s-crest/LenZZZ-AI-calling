import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from twilio_provider.app.api.routes_calls import router
from twilio_provider.app.api.deps import get_call_service
from twilio_provider.app.clients.twilio_client import CallResult
from twilio_provider.app.config import TwilioSettings, AppSettings
from twilio_provider.app.services.call_service import CallService


class FakeTwilioClient:
    """Stands in for the SDK wrapper: records what the service asked for."""

    def __init__(self, error: Exception | None = None):
        self.calls: list[dict] = []
        self.error = error

    async def create_call(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return CallResult(sid="CA" + "0" * 32, status="queued")


@pytest.fixture
def settings():
    return TwilioSettings(
        account_sid="ACtest", auth_token="tok", from_number="+14155550100",
        default_message="default hello", ring_timeout_seconds=25,
    )


@pytest.fixture
def app_settings():
    return AppSettings(
        public_base_url="https://test.ngrok.app",
        status_callback_url=None,
        request_timeout=10.0,
    )



@pytest.fixture
def make_client(settings, app_settings):
    def _make(error: Exception | None = None):
        fake = FakeTwilioClient(error)
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_call_service] = lambda: CallService(fake, settings, app_settings)
        return TestClient(app), fake
    return _make
