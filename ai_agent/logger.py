"""Clean logging processor for voice agent turns (STT, LLM, TTS)."""
import logging
from pipecat.frames.frames import (
    Frame,
    TextFrame,
    TranscriptionFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

logger = logging.getLogger("voice_agent")


class ConversationLogger(FrameProcessor):
    """Logs clean, high-visibility messages for STT, LLM, and TTS turns."""

    def __init__(self):
        super().__init__()
        self._current_assistant_text: list[str] = []

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, UserStartedSpeakingFrame):
            logger.info("🎤 User started speaking...")

        elif isinstance(frame, TranscriptionFrame):
            text = frame.text.strip()
            if text:
                logger.info(f"🎤 [STT] User: \"{text}\"")

        elif isinstance(frame, TextFrame):
            # Accumulate LLM output tokens/chunks
            if frame.text:
                self._current_assistant_text.append(frame.text)

        elif isinstance(frame, TTSStartedFrame):
            full_reply = "".join(self._current_assistant_text).strip()
            if full_reply:
                logger.info(f"🤖 [LLM Reply]: \"{full_reply}\"")
                self._current_assistant_text.clear()
            logger.info("🔊 [TTS] AI started speaking...")

        elif isinstance(frame, TTSStoppedFrame):
            logger.info("🔇 [TTS] AI finished speaking.")

        await self.push_frame(frame, direction)
