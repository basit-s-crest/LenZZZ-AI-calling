"""Twilio Media Streams WebSocket transport for the Pipecat voice pipeline.

Flow:
  Twilio call answered
    → Twilio POSTs to /twilio/voice/outbound  (routes_webhooks.py)
    → We return TwiML <Stream> pointing to wss://<host>/ws
    → Twilio opens this WebSocket and streams mulaw audio here
    → We feed audio into STT → LLM → TTS pipeline
    → Pipeline audio is serialized back to mulaw JSON and sent to Twilio
"""
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)

from ..pipeline import create_voice_pipeline
from telephony_service.twilio_provider.app.config import TwilioSettings

logger = logging.getLogger("voice_agent.twilio")
router = APIRouter(tags=["twilio-stream"])


def _load_twilio_settings() -> TwilioSettings | None:
    """Loads Twilio credentials from .env for auto hang-up support.
    Returns None if settings are unavailable (prevents startup failure).
    """
    try:
        return TwilioSettings()
    except Exception as exc:
        logger.warning("Twilio settings unavailable, auto hang-up disabled: %s", exc)
        return None


@router.websocket("/ws")
async def twilio_media_stream(websocket: WebSocket):
    """Twilio Media Streams WebSocket endpoint.

    Step 1 – Handshake: wait for Twilio's 'start' event to extract stream_sid / call_sid.
    Step 2 – Build: construct TwilioFrameSerializer with those IDs + credentials.
    Step 3 – Run:  wire the serializer into FastAPIWebsocketTransport and run the pipeline.
    """
    await websocket.accept()
    logger.info("Twilio WebSocket connected from %s", websocket.client)

    # ------------------------------------------------------------------
    # Step 1: Wait for the 'start' event – we need stream_sid before we
    # can build the serializer.  Twilio always sends 'connected' then
    # 'start' before any 'media' frames.
    # ------------------------------------------------------------------
    stream_sid: str | None = None
    call_sid: str | None = None

    try:
        async for raw in websocket.iter_text():
            msg = json.loads(raw)
            event = msg.get("event")

            if event == "connected":
                logger.debug("Twilio handshake: connected")
                continue

            if event == "start":
                stream_sid = msg["start"]["streamSid"]
                call_sid = msg["start"].get("callSid")
                logger.info(
                    "Twilio stream started — stream_sid=%s  call_sid=%s",
                    stream_sid,
                    call_sid,
                )
                break

            logger.warning("Unexpected Twilio event before 'start': %s", event)

    except WebSocketDisconnect:
        logger.info("Twilio disconnected before stream started")
        return

    if not stream_sid:
        logger.error("No stream_sid received from Twilio — closing connection")
        await websocket.close()
        return

    # ------------------------------------------------------------------
    # Step 2: Build the serializer.
    # TwilioFrameSerializer handles:
    #   • mulaw 8kHz ↔ PCM conversion
    #   • base64 encode/decode
    #   • JSON wrapping for Twilio media protocol
    #   • Interruption → Twilio 'clear' event
    #   • Auto hang-up on EndFrame/CancelFrame (if credentials are present)
    # ------------------------------------------------------------------
    twilio_settings = _load_twilio_settings()

    auto_hang_up = bool(
        call_sid
        and twilio_settings
        and twilio_settings.account_sid
        and twilio_settings.auth_token
    )

    serializer = TwilioFrameSerializer(
        stream_sid=stream_sid,
        call_sid=call_sid,
        account_sid=twilio_settings.account_sid if twilio_settings else None,
        auth_token=(
            twilio_settings.auth_token.get_secret_value()
            if twilio_settings and twilio_settings.auth_token
            else None
        ),
        params=TwilioFrameSerializer.InputParams(
            auto_hang_up=auto_hang_up,
        ),
    )

    # ------------------------------------------------------------------
    # Step 3: Build transport + run shared voice pipeline.
    # add_wav_header=False  — Twilio expects raw mulaw, not WAV-wrapped PCM.
    # ------------------------------------------------------------------
    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            vad_audio_passthrough=True,
            serializer=serializer,
            session_timeout=None,
        ),
    )

    try:
        task, runner = create_voice_pipeline(transport)
        await runner.add_workers(task)
        await runner.run()
    except WebSocketDisconnect:
        logger.info("Twilio media stream disconnected (call ended)")
    except Exception as exc:
        logger.error("Error in Twilio voice pipeline: %s", exc, exc_info=True)
        try:
            await websocket.close()
        except Exception:
            pass
