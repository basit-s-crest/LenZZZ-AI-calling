"""WebSocket transport endpoint for browser testing UI."""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import Frame, InputAudioRawFrame, OutputAudioRawFrame
from pipecat.serializers.base_serializer import FrameSerializer
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)

from ..pipeline import create_voice_pipeline

logger = logging.getLogger("voice_agent")
router = APIRouter(prefix="/ws", tags=["voice_agent"])


class RawAudioFrameSerializer(FrameSerializer):
    """Serializes and deserializes raw 16kHz PCM audio bytes directly for browser WebSockets."""

    async def serialize(self, frame: Frame) -> str | bytes | None:
        if isinstance(frame, OutputAudioRawFrame):
            return frame.audio
        return None

    async def deserialize(self, data: str | bytes) -> Frame | None:
        if isinstance(data, bytes) and len(data) > 0:
            return InputAudioRawFrame(
                audio=data,
                sample_rate=16000,
                num_channels=1,
            )
        return None


@router.websocket("/test-client")
async def websocket_test_client(websocket: WebSocket):
    """WebSocket endpoint connecting browser audio directly to the Pipecat pipeline."""
    await websocket.accept()
    logger.info("🟢 Browser audio client connected to voice agent.")

    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            vad_audio_passthrough=True,
            serializer=RawAudioFrameSerializer(),
            session_timeout=None,  # Do not drop connection while waiting for user to speak
        ),
    )

    try:
        task, runner = create_voice_pipeline(transport)
        await runner.add_workers(task)
        await runner.run()
    except WebSocketDisconnect:
        logger.info("🔴 Browser audio client disconnected.")
    except Exception as exc:
        logger.error(f"Error in voice pipeline: {exc}", exc_info=True)
        try:
            await websocket.close()
        except Exception:
            pass
