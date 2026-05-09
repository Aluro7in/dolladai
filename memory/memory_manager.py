"""
Memory Manager — persistent conversation history and long-term memory.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


MEMORY_DIR = os.path.expanduser("~/.ai_agent")
HISTORY_FILE = os.path.join(MEMORY_DIR, "conversation_history.json")
LONG_TERM_FILE = os.path.join(MEMORY_DIR, "long_term_memory.json")
PREFERENCES_FILE = os.path.join(MEMORY_DIR, "preferences.json")


def _ensure_dir():
    os.makedirs(MEMORY_DIR, exist_ok=True)


class ConversationMemory:
    """Manages conversation history with sliding window."""

    def __init__(self, max_messages: int = 50):
        _ensure_dir()
        self.max_messages = max_messages
        self.messages: List[Dict[str, str]] = []
        self._load()

    def _load(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    self.messages = json.load(f)
            except Exception:
                self.messages = []

    def _save(self):
        with open(HISTORY_FILE, "w") as f:
            json.dump(self.messages, f, indent=2)

    def add_message(self, role: str, content: str):
        """Add a message to history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        # Keep within window
        if len(self.messages) > self.max_messages:
            # Always keep system message if present
            system_msgs = [m for m in self.messages if m["role"] == "system"]
            other_msgs = [m for m in self.messages if m["role"] != "system"]
            other_msgs = other_msgs[-(self.max_messages - len(system_msgs)):]
            self.messages = system_msgs + other_msgs
        self._save()

    def get_messages_for_api(self) -> List[Dict]:
        """Return messages in API format (without timestamp)."""
        result = []
        for m in self.messages:
            msg: Dict = {"role": m["role"], "content": m.get("content", "") or ""}
            # Include tool_calls for assistant messages
            if m["role"] == "assistant" and m.get("tool_calls"):
                msg["tool_calls"] = m["tool_calls"]
            # Include tool metadata for tool messages
            if m["role"] == "tool":
                msg["tool_call_id"] = m.get("tool_call_id", "call_0")
                msg["name"] = m.get("name", "")
            result.append(msg)
        return result

    def clear(self):
        """Clear conversation history."""
        self.messages = []
        self._save()

    def get_summary(self) -> str:
        """Get a brief summary of conversation stats."""
        user_msgs = sum(1 for m in self.messages if m["role"] == "user")
        assistant_msgs = sum(1 for m in self.messages if m["role"] == "assistant")
        return f"{user_msgs} user messages, {assistant_msgs} assistant messages in history."


class LongTermMemory:
    """Stores important facts and user preferences persistently."""

    def __init__(self):
        _ensure_dir()
        self.facts: List[Dict] = []
        self.preferences: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if os.path.exists(LONG_TERM_FILE):
            try:
                with open(LONG_TERM_FILE, "r") as f:
                    self.facts = json.load(f)
            except Exception:
                self.facts = []
        if os.path.exists(PREFERENCES_FILE):
            try:
                with open(PREFERENCES_FILE, "r") as f:
                    self.preferences = json.load(f)
            except Exception:
                self.preferences = {}

    def _save(self):
        with open(LONG_TERM_FILE, "w") as f:
            json.dump(self.facts, f, indent=2)
        with open(PREFERENCES_FILE, "w") as f:
            json.dump(self.preferences, f, indent=2)

    def remember(self, fact: str, category: str = "general"):
        """Store a fact in long-term memory."""
        self.facts.append({
            "fact": fact,
            "category": category,
            "timestamp": datetime.now().isoformat(),
        })
        self._save()
        return f"Remembered: {fact}"

    def recall(self, query: str = "") -> List[Dict]:
        """Recall facts, optionally filtered by query."""
        if not query:
            return self.facts
        return [f for f in self.facts if query.lower() in f["fact"].lower() or query.lower() in f["category"].lower()]

    def forget(self, query: str):
        """Remove facts matching query."""
        before = len(self.facts)
        self.facts = [f for f in self.facts if query.lower() not in f["fact"].lower()]
        self._save()
        return f"Removed {before - len(self.facts)} facts."

    def set_preference(self, key: str, value: Any):
        """Set a user preference."""
        self.preferences[key] = value
        self._save()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self.preferences.get(key, default)

    def get_context_string(self) -> str:
        """Get a formatted string of important memories for system prompt."""
        if not self.facts:
            return ""
        recent = self.facts[-20:]  # Last 20 facts
        lines = ["## Long-term Memory:"]
        for f in recent:
            lines.append(f"- [{f['category']}] {f['fact']}")
        return "\n".join(lines)
