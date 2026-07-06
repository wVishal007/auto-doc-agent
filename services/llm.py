import httpx

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseLanguageModel
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_mistralai import ChatMistralAI
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


def extract_text_or_raise(response) -> str:
    text = extract_text(response).strip()
    if not text:
        raise ValueError("Empty LLM response — model returned no text content")
    return text


def get_provider_info(model_name: str) -> tuple:
    if model_name.startswith("nvidia/"):
        return ("NVIDIA", model_name)
    if model_name.startswith("mistral"):
        return ("Mistral", model_name)
    return ("Google", model_name)


def create_llm(model_name: str, temperature: float = None) -> BaseLanguageModel:
    temp = temperature if temperature is not None else settings.temperature

    if model_name.startswith("nvidia/"):
        if not settings.nvidia_api_key:
            raise ValueError("NVIDIA_API_KEY is not set. Add NVIDIA_API_KEY=your_key to .env")
        return ChatNVIDIA(
            model=model_name,
            api_key=settings.nvidia_api_key,
            temperature=temp,
            top_p=0.95,
            max_completion_tokens=settings.nvidia_max_tokens,
            timeout=settings.request_timeout,
        )

    if model_name.startswith("mistral"):
        if not settings.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY is not set. Add MISTRAL_API_KEY=your_key to .env")
        return ChatMistralAI(
            model=model_name,
            mistral_api_key=settings.mistral_api_key,
            temperature=temp,
            max_tokens=settings.mistral_max_tokens,
            timeout=settings.request_timeout,
        )

    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set. Add GEMINI_API_KEY=your_key to .env")
    _client_google = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.gemini_api_key,
        temperature=temp,
        timeout=settings.request_timeout,
        client_args={"timeout": httpx.Timeout(settings.request_timeout)},
    )
    _resolved_timeout = _client_google.client._api_client._httpx_client.timeout
    print(f"  [Google] resolved http client timeout={_resolved_timeout}")
    return _client_google
