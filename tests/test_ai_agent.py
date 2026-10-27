"""Tests for AI voice agent configuration and FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient

from ai_agent.config import VoiceAgentSettings, get_voice_settings
from ai_agent.prompts import SYSTEM_PROMPT
from main import app


def test_voice_agent_settings():
    """Verify settings can be loaded."""
    settings = get_voice_settings()
    assert isinstance(settings, VoiceAgentSettings)
    assert settings.groq_model == "openai/gpt-oss-120b"
    assert settings.deepgram_stt_model == "nova-3-general"


def test_system_prompt_present():
    """Verify voice system prompt is defined and conversational."""
    assert len(SYSTEM_PROMPT) > 50
    assert "voice assistant" in SYSTEM_PROMPT.lower()


def test_fastapi_endpoints():
    """Verify health and static UI routes work."""
    client = TestClient(app)
    # Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"ok": True}

    # Testing UI root
    ui_res = client.get("/")
    assert ui_res.status_code == 200
    assert "Pipecat AI Voice Agent" in ui_res.text
