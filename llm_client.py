"""
DolladAI — Universal LLM Client
Supports: Blackbox AI (default), OpenAI, Anthropic Claude, Google Gemini,
          Groq, OpenRouter, Ollama, xAI Grok, Qwen (Alibaba DashScope)
All providers use OpenAI-compatible /v1/chat/completions unless noted.
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional

# ── Load .env file ──────────────────────────────────────────────────────────
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

# ── Default Blackbox credentials ────────────────────────────────────────────
BLACKBOX_API_KEY  = os.environ.get("BLACKBOX_API_KEY", "")
BLACKBOX_BASE_URL = "https://api.blackbox.ai/v1/chat/completions"

# ── Provider registry ────────────────────────────────────────────────────────
# Each entry: { base_url, default_model, auth_header, notes }
PROVIDERS: Dict[str, Dict] = {
    "blackbox": {
        "name":          "Blackbox AI",
        "base_url":      "https://api.blackbox.ai/v1/chat/completions",
        "models_url":    "https://api.blackbox.ai/v1/models",
        "default_model": "blackboxai/blackbox-pro",
        "auth_scheme":   "Bearer",
        "docs_url":      "https://blackbox.ai",
        "models": {
            "blackbox-pro":  "blackboxai/blackbox-pro",
            "gpt4":          "blackboxai/openai/gpt-5.3-codex",
            "claude":        "blackboxai/anthropic/claude-sonnet-4.6",
            "gemini":        "blackboxai/google/gemini-3.1-pro-preview",
            "kimi":          "blackboxai/moonshotai/kimi-k2.6",
            "grok":          "blackboxai/x-ai/grok-code-fast-1:free",
        },
    },
    "openai": {
        "name":          "OpenAI",
        "base_url":      "https://api.openai.com/v1/chat/completions",
        "models_url":    "https://api.openai.com/v1/models",
        "default_model": "gpt-4o",
        "auth_scheme":   "Bearer",
        "docs_url":      "https://platform.openai.com/api-keys",
        "models": {
            "gpt-4o":          "gpt-4o",
            "gpt-4o-mini":     "gpt-4o-mini",
            "gpt-4-turbo":     "gpt-4-turbo",
            "gpt-3.5-turbo":   "gpt-3.5-turbo",
            "o1":              "o1",
            "o1-mini":         "o1-mini",
        },
    },
    "anthropic": {
        "name":          "Anthropic Claude",
        "base_url":      "https://api.anthropic.com/v1/messages",
        "models_url":    None,
        "default_model": "claude-3-5-sonnet-20241022",
        "auth_scheme":   "x-api-key",   # special header
        "docs_url":      "https://console.anthropic.com/settings/keys",
        "models": {
            "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku":  "claude-3-5-haiku-20241022",
            "claude-3-opus":     "claude-3-opus-20240229",
            "claude-3-sonnet":   "claude-3-sonnet-20240229",
            "claude-3-haiku":    "claude-3-haiku-20240307",
        },
    },
    "gemini": {
        "name":          "Google Gemini",
        "base_url":      "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "models_url":    None,
        "default_model": "gemini-2.0-flash",
        "auth_scheme":   "Bearer",
        "docs_url":      "https://aistudio.google.com/app/apikey",
        "models": {
            "gemini-2.0-flash":       "gemini-2.0-flash",
            "gemini-2.0-flash-lite":  "gemini-2.0-flash-lite",
            "gemini-1.5-pro":         "gemini-1.5-pro",
            "gemini-1.5-flash":       "gemini-1.5-flash",
        },
    },
    "groq": {
        "name":          "Groq",
        "base_url":      "https://api.groq.com/openai/v1/chat/completions",
        "models_url":    "https://api.groq.com/openai/v1/models",
        "default_model": "llama-3.3-70b-versatile",
        "auth_scheme":   "Bearer",
        "docs_url":      "https://console.groq.com/keys",
        "models": {
            "llama-3.3-70b":       "llama-3.3-70b-versatile",
            "llama-3.1-8b":        "llama-3.1-8b-instant",
            "llama-3.1-70b":       "llama-3.1-70b-versatile",
            "mixtral-8x7b":        "mixtral-8x7b-32768",
            "gemma2-9b":           "gemma2-9b-it",
            "deepseek-r1-70b":     "deepseek-r1-distill-llama-70b",
        },
    },
    "openrouter": {
        "name":          "OpenRouter",
        "base_url":      "https://openrouter.ai/api/v1/chat/completions",
        "models_url":    "https://openrouter.ai/api/v1/models",
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
        "auth_scheme":   "Bearer",
        "docs_url":      "https://openrouter.ai/keys",
        "models": {
            "llama-3.3-70b-free":    "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek-r1-free":      "deepseek/deepseek-r1:free",
            "gemma-3-27b-free":      "google/gemma-3-27b-it:free",
            "qwen-2.5-72b-free":     "qwen/qwen-2.5-72b-instruct:free",
            "mistral-7b-free":       "mistralai/mistral-7b-instruct:free",
            "claude-3.5-sonnet":     "anthropic/claude-3.5-sonnet",
            "gpt-4o":                "openai/gpt-4o",
            "gemini-2.0-flash":      "google/gemini-2.0-flash-001",
        },
    },
    "ollama": {
        "name":          "Ollama (Local)",
        "base_url":      "http://localhost:11434/v1/chat/completions",
        "models_url":    "http://localhost:11434/api/tags",
        "default_model": "llama3.2",
        "auth_scheme":   "Bearer",
        "docs_url":      "https://ollama.com",
        "models": {
            "llama3.2":    "llama3.2",
            "llama3.1":    "llama3.1",
            "mistral":     "mistral",
            "codellama":   "codellama",
            "phi3":        "phi3",
            "gemma2":      "gemma2",
            "qwen2.5":     "qwen2.5",
            "deepseek-r1": "deepseek-r1",
        },
    },
    "grok": {
        "name":          "xAI Grok",
        "base_url":      "https://api.x.ai/v1/chat/completions",
        "models_url":    "https://api.x.ai/v1/models",
        "default_model": "grok-3",
        "auth_scheme":   "Bearer",
        "docs_url":      "https://console.x.ai",
        "models": {
            "grok-3":        "grok-3",
            "grok-3-mini":   "grok-3-mini",
            "grok-2":        "grok-2-1212",
            "grok-2-vision": "grok-2-vision-1212",
        },
    },
    "qwen": {
        "name":          "Qwen (Alibaba)",
        "base_url":      "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "models_url":    None,
        "default_model": "qwen-max",
        "auth_scheme":   "Bearer",
        "docs_url":      "https://dashscope.console.aliyun.com/apiKey",
        "models": {
            "qwen-max":        "qwen-max",
            "qwen-plus":       "qwen-plus",
            "qwen-turbo":      "qwen-turbo",
            "qwen2.5-72b":     "qwen2.5-72b-instruct",
            "qwen2.5-coder":   "qwen2.5-coder-32b-instruct",
        },
    },
}

# Blackbox shorthand model map (legacy support)
BLACKBOX_MODELS = PROVIDERS["blackbox"]["models"]


class UniversalLLMClient:
    """
    Universal LLM client supporting multiple providers.
    Falls back to Blackbox AI when no custom key is configured.
    """

    def __init__(
        self,
        model: str = "default",
        temperature: float = 0.7,
        provider: str = "blackbox",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.temperature = temperature
        self.provider = provider
        self._custom_api_key = api_key  # user-supplied key (never logged)
        self._custom_base_url = base_url

        self._resolve_provider_config()
        self._resolve_model(model)

    def _resolve_provider_config(self):
        """Set base_url and api_key from provider config."""
        pconf = PROVIDERS.get(self.provider, PROVIDERS["blackbox"])

        # Base URL: custom override > provider default
        self.base_url = self._custom_base_url or pconf["base_url"]

        # API key: custom > env var > blackbox default
        if self._custom_api_key:
            self.api_key = self._custom_api_key
        elif self.provider == "blackbox":
            self.api_key = BLACKBOX_API_KEY
        else:
            # Try env var like OPENAI_API_KEY, GROQ_API_KEY, etc.
            env_key = f"{self.provider.upper()}_API_KEY"
            self.api_key = os.environ.get(env_key, "")

        self.auth_scheme = pconf.get("auth_scheme", "Bearer")

    def _resolve_model(self, model: str):
        """Resolve model alias to full model ID."""
        pconf = PROVIDERS.get(self.provider, PROVIDERS["blackbox"])
        model_map = pconf.get("models", {})

        if model in ("default", ""):
            self.model = pconf["default_model"]
        elif model in model_map:
            self.model = model_map[model]
        else:
            # Use as-is (user may pass full model ID)
            self.model = model

    def _build_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.auth_scheme == "x-api-key":
            # Anthropic native format
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"
        else:
            headers["Authorization"] = f"Bearer {self.api_key}"
        # OpenRouter requires these
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://dolladai.app"
            headers["X-Title"] = "DolladAI"
        return headers

    def _build_payload(self, messages: List[Dict], tools: Optional[List[Dict]]) -> Dict:
        """Build request payload, handling provider quirks."""
        if self.provider == "anthropic":
            # Anthropic native API format
            system_msgs = [m for m in messages if m["role"] == "system"]
            other_msgs  = [m for m in messages if m["role"] != "system"]
            payload: Dict[str, Any] = {
                "model":      self.model,
                "max_tokens": 4096,
                "messages":   other_msgs,
            }
            if system_msgs:
                payload["system"] = system_msgs[0]["content"]
            if tools:
                # Convert OpenAI tool format to Anthropic format
                payload["tools"] = [
                    {
                        "name":         t["function"]["name"],
                        "description":  t["function"].get("description", ""),
                        "input_schema": t["function"].get("parameters", {}),
                    }
                    for t in tools
                ]
        else:
            payload = {
                "model":       self.model,
                "messages":    messages,
                "temperature": self.temperature,
            }
            if tools:
                payload["tools"]       = tools
                payload["tool_choice"] = "auto"
        return payload

    def _normalize_response(self, raw: Dict, provider: str) -> Dict:
        """Normalize Anthropic response to OpenAI format."""
        if provider != "anthropic":
            return raw
        # Anthropic → OpenAI shape
        content = ""
        tool_calls = []
        for block in raw.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append({
                    "id": block.get("id", "call_0"),
                    "type": "function",
                    "function": {
                        "name":      block.get("name", ""),
                        "arguments": json.dumps(block.get("input", {})),
                    },
                })
        msg: Dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        return {
            "choices": [{"message": msg, "finish_reason": raw.get("stop_reason", "stop")}],
            "model":   raw.get("model", self.model),
            "usage":   raw.get("usage", {}),
        }

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Send a chat request to the configured provider."""
        headers = self._build_headers()
        payload  = self._build_payload(messages, tools)

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            raw = response.json()
            return self._normalize_response(raw, self.provider)

        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, "status_code", 0)
            if status == 401:
                return {"error": f"Invalid API key for {PROVIDERS.get(self.provider,{}).get('name', self.provider)}. Please check your key."}
            if status == 429:
                return {"error": "Rate limit exceeded. Please wait a moment and try again."}
            if status == 402:
                return {"error": "Insufficient credits / quota exceeded for this API key."}
            return {"error": f"HTTP {status}: {e}"}
        except requests.exceptions.ConnectionError:
            if self.provider == "ollama":
                return {"error": "Cannot connect to Ollama. Make sure Ollama is running locally (ollama serve)."}
            return {"error": "Connection error. Check your internet connection."}
        except requests.exceptions.Timeout:
            return {"error": "Request timed out (120s). Try a faster model."}
        except Exception as e:
            return {"error": str(e)}

    def extract_reply(self, response: Dict[str, Any]) -> str:
        if "error" in response:
            return f"[LLM Error] {response['error']}"
        try:
            choices = response.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                return msg.get("content", "") or ""
        except Exception:
            pass
        return response.get("content", response.get("text", str(response)))

    def extract_tool_calls(self, response: Dict[str, Any]) -> List[Dict]:
        try:
            choices = response.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                return msg.get("tool_calls", []) or []
        except Exception:
            pass
        return []

    def switch_model(self, model: str):
        self._resolve_model(model)
        print(f"[LLM] Switched to model: {self.model} (provider: {self.provider})")

    def switch_provider(self, provider: str, api_key: str, model: str = "default", base_url: str = ""):
        """Hot-swap provider + key at runtime."""
        self.provider = provider
        self._custom_api_key  = api_key or None
        self._custom_base_url = base_url or None
        self._resolve_provider_config()
        self._resolve_model(model)
        print(f"[LLM] Switched provider → {provider}, model → {self.model}")

    @property
    def display_name(self) -> str:
        pname = PROVIDERS.get(self.provider, {}).get("name", self.provider)
        return f"{pname} / {self.model}"

    @staticmethod
    def get_providers_info() -> List[Dict]:
        """Return provider list for the UI (no secrets)."""
        result = []
        for pid, pconf in PROVIDERS.items():
            result.append({
                "id":            pid,
                "name":          pconf["name"],
                "default_model": pconf["default_model"],
                "docs_url":      pconf["docs_url"],
                "models":        list(pconf["models"].keys()),
            })
        return result


# ── Backwards-compat alias ───────────────────────────────────────────────────
BlackboxLLMClient = UniversalLLMClient
