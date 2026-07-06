import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    nvidia_api_key: str = ""
    mistral_api_key: str = ""

    planner_model: str = "mistral-small-latest"
    generator_model: str = "mistral-small-latest"
    reflector_model: str = "mistral-small-latest"
    fallback_model: str = "mistral-large-latest"

    temperature: float = 0.3
    request_timeout: int = 120
    nvidia_max_tokens: int = 8192
    mistral_max_tokens: int = 8192

    output_dir: str = "generated_docs"
    app_title: str = "Autonomous Agent API"
    app_version: str = "1.0.0"

    class Config:
        env_file = ".env"


settings = Settings()

os.makedirs(settings.output_dir, exist_ok=True)


def _detect_provider(model: str) -> str:
    if model.startswith("nvidia/"):
        return "NVIDIA NIM"
    if model.startswith("mistral"):
        return "Mistral AI"
    return "Google AI Studio"


def _key_status(model: str) -> str:
    if model.startswith("nvidia/"):
        return "OK" if settings.nvidia_api_key else "MISSING API KEY"
    if model.startswith("mistral"):
        return "OK" if settings.mistral_api_key else "MISSING API KEY"
    return "OK" if settings.gemini_api_key else "MISSING API KEY"


def _print_config():
    roles = [
        ("Planner", settings.planner_model),
        ("Generator", settings.generator_model),
        ("Reflector", settings.reflector_model),
        ("Fallback", settings.fallback_model),
    ]

    print()
    print("=" * 50)
    print(" Agent Configuration")
    print("=" * 50)
    for role, model in roles:
        print(f"  Role: {role}")
        print(f"  Provider: {_detect_provider(model)}")
        print(f"  Model: {model}")
        print(f"  Status: {_key_status(model)}")
        print()
    print("=" * 50)
    print()


_print_config()
