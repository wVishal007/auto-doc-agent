from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseLanguageModel
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from config import settings


def extract_text(response) -> str:
    content = response.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
            elif hasattr(item, "type"):
                if getattr(item, "type", None) == "text":
                    parts.append(getattr(item, "text", ""))
            elif hasattr(item, "text"):
                parts.append(item.text)
            else:
                parts.append(str(item))
        return " ".join(parts)
    return str(content)


def _google_llm(model: str, temperature: float) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=settings.gemini_api_key,
        temperature=temperature,
    )


def _nvidia_llm(model: str, temperature: float) -> ChatNVIDIA:
    return ChatNVIDIA(
        model=model,
        api_key=settings.nvidia_api_key,
        temperature=temperature,
        top_p=0.95,
        max_completion_tokens=settings.nvidia_max_tokens,
    )


def get_llm(task: str = "content", temperature: float = 0.3) -> BaseLanguageModel:
    if task == "planner":
        return _google_llm(settings.planner_model, temperature)

    if task == "content":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        return _google_llm(settings.content_model, temperature)

    if task == "fallback":
        if not settings.nvidia_api_key:
            raise ValueError(
                "NVIDIA_API_KEY is not set. "
                "Add NVIDIA_API_KEY=your_key to .env"
            )
        return _nvidia_llm(settings.fallback_model, temperature)

    if task == "reflector":
        return _google_llm(settings.reflector_model, temperature)

    raise ValueError(f"Unknown task: {task}. Use planner, content, fallback, or reflector.")
