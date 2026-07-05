import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    nvidia_api_key: str = ""

    planner_model: str = "gemini-3.1-flash-lite"
    content_model: str = "gemma-4-31b-it"
    reflector_model: str = "gemini-3.1-flash-lite"
    fallback_model: str = "nvidia/nemotron-3-ultra-550b-a55b"

    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_max_tokens: int = 16384

    output_dir: str = "generated_docs"
    app_title: str = "Autonomous Agent API"
    app_version: str = "1.0.0"

    class Config:
        env_file = ".env"


settings = Settings()

os.makedirs(settings.output_dir, exist_ok=True)
