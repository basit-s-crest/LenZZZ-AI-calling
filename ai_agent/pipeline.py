"""Core Pipecat pipeline builder connecting STT, LLM, and TTS."""
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_response_universal import (
    LLMAssistantAggregator,
    LLMContext,
    LLMUserAggregator,
)

from .logger import ConversationLogger
from .prompts import SYSTEM_PROMPT
from .providers.llm import get_llm_service
from .providers.stt import get_stt_service
from .providers.tts import get_tts_service


def create_voice_pipeline(transport) -> tuple[PipelineTask, PipelineRunner]:
    """Assembles a modular Pipecat pipeline for any transport (Browser WS or Twilio)."""
    stt = get_stt_service()
    llm = get_llm_service()
    tts = get_tts_service()
    conversation_logger = ConversationLogger()

    # Conversation context with voice-optimized system prompt
    context = LLMContext(messages=[{"role": "system", "content": SYSTEM_PROMPT}])
    context_user = LLMUserAggregator(context)
    context_assistant = LLMAssistantAggregator(context)

    # Streaming linear pipeline:
    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            context_user,
            llm,
            tts,
            conversation_logger,
            transport.output(),
            context_assistant,
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
        ),
    )

    runner = PipelineRunner(handle_sigint=False)
    return task, runner
