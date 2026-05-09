"""
Blackbox LLM Client
Handles all communication with the Blackbox AI API.
"""

import json
import requests
from typing import List, Dict, Any, Optional


BLACKBOX_API_KEY = "sk-Nd7JGWbYMnVS7Td1tkSH6Q"
BLACKBOX_BASE_URL = "https://api.blackbox.ai/v1/chat/completions"

MODELS = {
    "default":  "blackboxai/blackbox-pro",
    "gpt4":     "blackboxai/openai/gpt-5.3-codex",
    "claude":   "blackboxai/anthropic/claude-sonnet-4.6",
    "gemini":   "blackboxai/google/gemini-3.1-pro-preview",
    "deepseek": "blackboxai/moonshotai/kimi-k2.6",
    "grok":     "blackboxai/x-ai/grok-code-fast-1:free",
}


class BlackboxLLMClient:
    """Client for the Blackbox AI API."""

    def __init__(self, model: str = "default", temperature: float = 0.7):
        self.api_key = BLACKBOX_API_KEY
        self.model = MODELS.get(model, model)
        self.temperature = temperature
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Send a chat request to Blackbox API."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            response = requests.post(
                BLACKBOX_BASE_URL,
                headers=self.headers,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            return {"error": f"HTTP Error: {e}"}
        except requests.exceptions.ConnectionError:
            return {"error": "Connection error. Check your internet connection."}
        except requests.exceptions.Timeout:
            return {"error": "Request timed out."}
        except Exception as e:
            return {"error": str(e)}

    def extract_reply(self, response: Dict[str, Any]) -> str:
        """Extract the assistant text reply from an API response."""
        if "error" in response:
            return f"[LLM Error] {response['error']}"
        try:
            choices = response.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                return msg.get("content", "") or ""
        except Exception:
            pass
        # Fallback: try common response shapes
        return response.get("content", response.get("text", str(response)))

    def extract_tool_calls(self, response: Dict[str, Any]) -> List[Dict]:
        """Extract tool calls from an API response."""
        try:
            choices = response.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                return msg.get("tool_calls", []) or []
        except Exception:
            pass
        return []

    def switch_model(self, model: str):
        """Switch the active model."""
        self.model = MODELS.get(model, model)
        print(f"[LLM] Switched to model: {self.model}")
