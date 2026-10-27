"""Configuration settings for AI Voice Agent."""
from pydantic import SecretStr
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class VoiceAgentSettings(BaseSettings):
    # .env file takes priority over system environment variables.
    # This prevents stale/old system-level API keys from overriding the project .env.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Put dotenv (.env file) BEFORE system env so .env always wins
        return init_settings, dotenv_settings, env_settings, file_secret_settings

    # LLM (Groq)
    groq_api_key: SecretStr | None = None
    groq_model: str = "openai/gpt-oss-120b"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # STT (Deepgram)
    deepgram_api_key: SecretStr | None = None
    deepgram_stt_model: str = "nova-3-general"
    deepgram_language: str = "en"

    # TTS (Cartesia or Deepgram Aura fallback)
    cartesia_api_key: SecretStr | None = None
    cartesia_voice_id: str = "db6b0ed5-d5d3-463d-ae85-518a07d3c2b4"  # Skylar - Friendly Guide
    deepgram_tts_voice: str = "aura-asteria-en"


def get_voice_settings() -> VoiceAgentSettings:
    return VoiceAgentSettings()

