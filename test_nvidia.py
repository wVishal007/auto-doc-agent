"""
NVIDIA Nemotron 3 - Connection Test
Tries multiple approaches to find what works with your API key.
"""

import os
import sys

env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVIDIA_KEY")
if not API_KEY:
    print("ERROR: Set NVIDIA_API_KEY in .env or as environment variable")
    sys.exit(1)

BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL_NAMES = [
    "nvidia/nemotron-3-ultra-550b-a55b",
    "nemotron-3-ultra-550b-a55b",
    "NVIDIA-Nemotron-3-Ultra-550B-A55B-NVFP4",
]

results = []

def ok(text):
    return f"[OK] {text}"

def fail(text):
    return f"[FAIL] {text}"

# -- Approach 1: ChatOpenAI --
print("=" * 60)
print("APPROACH 1: ChatOpenAI via integrate.api.nvidia.com/v1")
print("=" * 60)

try:
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    for model_name in MODEL_NAMES:
        try:
            r = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Say 'hello' in one word"}],
                max_tokens=20,
                temperature=0.1,
            )
            text = r.choices[0].message.content
            results.append(("ChatOpenAI", model_name, "OK", text))
            print(f"  {ok(model_name + ' -> ' + text)}")
        except Exception as e:
            code = getattr(e, "status_code", "?")
            results.append(("ChatOpenAI", model_name, f"FAIL ({code})", str(e)[:100]))
            print(f"  {fail(model_name + ' -> ' + str(e)[:80])}")
except ImportError:
    print("  [SKIP] openai not installed")
except Exception as e:
    print(f"  [ERROR] {e}")

# -- Approach 2: ChatNVIDIA (default) --
print()
print("=" * 60)
print("APPROACH 2: ChatNVIDIA (default api.nvidia.com)")
print("=" * 60)

try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
    for model_name in MODEL_NAMES:
        try:
            llm = ChatNVIDIA(
                model=model_name,
                api_key=API_KEY,
                temperature=0.1,
                max_completion_tokens=20,
            )
            r = llm.invoke([("user", "Say 'hello' in one word")])
            text = r.content if isinstance(r.content, str) else str(r.content)
            results.append(("ChatNVIDIA (default)", model_name, "OK", text[:50]))
            print(f"  {ok(model_name + ' -> ' + text[:50])}")
        except Exception as e:
            code = getattr(e, "status_code", "?")
            results.append(("ChatNVIDIA (default)", model_name, f"FAIL ({code})", str(e)[:100]))
            print(f"  {fail(model_name + ' -> ' + str(e)[:80])}")
except ImportError:
    print("  [SKIP] langchain_nvidia_ai_endpoints not installed")
except Exception as e:
    print(f"  [ERROR] {e}")

# -- Approach 3: ChatNVIDIA with base_url --
print()
print("=" * 60)
print("APPROACH 3: ChatNVIDIA with custom base_url")
print("=" * 60)

try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
    for model_name in MODEL_NAMES:
        try:
            llm = ChatNVIDIA(
                model=model_name,
                api_key=API_KEY,
                base_url=BASE_URL,
                temperature=0.1,
                max_completion_tokens=20,
            )
            r = llm.invoke([("user", "Say 'hello' in one word")])
            text = r.content if isinstance(r.content, str) else str(r.content)
            results.append(("ChatNVIDIA (custom base_url)", model_name, "OK", text[:50]))
            print(f"  {ok(model_name + ' -> ' + text[:50])}")
        except Exception as e:
            code = getattr(e, "status_code", "?")
            results.append(("ChatNVIDIA (custom base_url)", model_name, f"FAIL ({code})", str(e)[:100]))
            print(f"  {fail(model_name + ' -> ' + str(e)[:80])}")
except ImportError:
    print("  [SKIP] langchain_nvidia_ai_endpoints not installed")
except Exception as e:
    print(f"  [ERROR] {e}")

# -- Summary --
print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"{'Approach':<30} {'Model':<42} {'Status':<10}")
print("-" * 82)
for approach, model, status, msg in results:
    print(f"{approach:<30} {model:<42} {status:<10}")
    if status != "OK":
        print(f"{'':<30} {'':<42} {msg:<50}")

print()
print("UPDATE config.py with the working combination above.")
print("Then set llm_provider/fallback_model accordingly.")
