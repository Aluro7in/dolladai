"""
Agent Core — orchestrates LLM + tools + memory for the AI agent.
"""

import json
import re
from typing import Dict, Any, List, Optional

from llm_client import UniversalLLMClient as BlackboxLLMClient
from memory.memory_manager import ConversationMemory, LongTermMemory
from tools.file_tool import FileTool
from tools.web_tool import WebTool
from tools.code_tool import CodeTool
from tools.task_tool import TaskTool
from tools.system_tool import SystemTool
from tools.calendar_tool import CalendarTool
from tools.note_tool import NoteTool
from tools.search_tool import SearchTool


SYSTEM_PROMPT = """You are an advanced AI personal assistant with access to powerful tools. You can:

🗂️  **File Management** — read, write, list, search, move, copy files and directories
🌐  **Web Browsing** — fetch web pages, scrape content, download files
💻  **Code Execution** — run Python code, shell commands, install packages
✅  **Task Manager** — manage a persistent to-do list with priorities and due dates
📅  **Calendar** — schedule events, reminders, view upcoming events
📝  **Notes** — create, search, and manage personal notes
🔍  **Web Search** — search DuckDuckGo and Wikipedia
💻  **System Info** — CPU, memory, disk, processes, environment variables
🧠  **Memory** — remember important facts across conversations

## Guidelines:
- Always use the most appropriate tool for the task
- Be proactive: if a task requires multiple steps, execute them all
- When writing code, test it by running it
- For complex tasks, break them into steps and execute each one
- Remember important user preferences and facts
- Be concise but thorough in your responses
- If a tool fails, try an alternative approach

## Special Commands (user can type these):
- `/remember <fact>` — store something in long-term memory
- `/recall [query]` — recall stored memories
- `/forget <query>` — remove memories matching query
- `/clear` — clear conversation history
- `/tasks` — list all tasks
- `/notes` — list all notes
- `/calendar` — show today's events
- `/model <name>` — switch LLM model (default, gpt4, claude, gemini, deepseek)
- `/help` — show available commands
- `/exit` — exit the agent

You have persistent memory across sessions. Use it wisely to provide personalized assistance.
"""


class AIAgent:
    """Main AI Agent that orchestrates everything."""

    def __init__(self, model: str = "default", verbose: bool = False):
        self.llm = BlackboxLLMClient(model=model)
        self.memory = ConversationMemory(max_messages=60)
        self.long_term = LongTermMemory()
        self.verbose = verbose

        # Initialize tools
        self.tools = {
            "file_manager": FileTool(),
            "web_browser": WebTool(),
            "code_executor": CodeTool(),
            "task_manager": TaskTool(),
            "system_info": SystemTool(),
            "calendar": CalendarTool(),
            "note_manager": NoteTool(),
            "web_search": SearchTool(),
        }

        # Tool schemas for LLM
        self.tool_schemas = [
            FileTool.SCHEMA,
            WebTool.SCHEMA,
            CodeTool.SCHEMA,
            TaskTool.SCHEMA,
            SystemTool.SCHEMA,
            CalendarTool.SCHEMA,
            NoteTool.SCHEMA,
            SearchTool.SCHEMA,
        ]

        # Initialize system message
        self._init_system_message()

    def _init_system_message(self):
        """Set up the system message with long-term memory context."""
        system_content = SYSTEM_PROMPT
        memory_context = self.long_term.get_context_string()
        if memory_context:
            system_content += f"\n\n{memory_context}"

        # Replace or add system message
        system_msgs = [m for m in self.memory.messages if m["role"] == "system"]
        if system_msgs:
            system_msgs[0]["content"] = system_content
        else:
            self.memory.messages.insert(0, {
                "role": "system",
                "content": system_content,
                "timestamp": "init",
            })

    def handle_special_command(self, user_input: str) -> Optional[str]:
        """Handle special slash commands."""
        cmd = user_input.strip().lower()

        if cmd == "/help":
            return """
🤖 **AI Agent Commands:**

**Memory:**
  `/remember <fact>` — store a fact in long-term memory
  `/recall [query]`  — recall stored memories
  `/forget <query>`  — remove memories matching query

**Quick Views:**
  `/tasks`           — list all pending tasks
  `/notes`           — list all notes
  `/calendar`        — show today's calendar events

**Model:**
  `/model <name>`    — switch model (default, gpt4, claude, gemini, deepseek)
  `/model`           — show current model

**Session:**
  `/clear`           — clear conversation history
  `/history`         — show conversation stats
  `/exit` or `/quit` — exit the agent

**Just chat naturally for everything else!**
"""

        elif cmd.startswith("/remember "):
            fact = user_input[10:].strip()
            result = self.long_term.remember(fact)
            self._init_system_message()
            return f"✅ {result}"

        elif cmd.startswith("/recall"):
            query = user_input[7:].strip()
            facts = self.long_term.recall(query)
            if not facts:
                return "🧠 No memories found."
            lines = ["🧠 **Memories:**"]
            for f in facts:
                lines.append(f"  [{f['category']}] {f['fact']} _(saved {f['timestamp'][:10]})_")
            return "\n".join(lines)

        elif cmd.startswith("/forget "):
            query = user_input[8:].strip()
            result = self.long_term.forget(query)
            return f"🗑️ {result}"

        elif cmd == "/clear":
            self.memory.clear()
            self._init_system_message()
            return "🧹 Conversation history cleared."

        elif cmd == "/history":
            return f"📊 {self.memory.get_summary()}"

        elif cmd == "/tasks":
            tool = self.tools["task_manager"]
            result = tool.run(action="list", filter_status="pending")
            tasks = result.get("tasks", [])
            if not tasks:
                return "✅ No pending tasks!"
            lines = [f"📋 **Pending Tasks ({len(tasks)}):**"]
            for t in tasks:
                due = f" (due: {t['due_date']})" if t.get("due_date") else ""
                lines.append(f"  #{t['id']} [{t['priority'].upper()}] {t['title']}{due}")
            return "\n".join(lines)

        elif cmd == "/notes":
            tool = self.tools["note_manager"]
            result = tool.run(action="list")
            notes = result.get("notes", [])
            if not notes:
                return "📝 No notes yet."
            lines = [f"📝 **Notes ({len(notes)}):**"]
            for n in notes:
                tags = f" [{', '.join(n['tags'])}]" if n.get("tags") else ""
                lines.append(f"  #{n['id']} {n['title']}{tags}")
            return "\n".join(lines)

        elif cmd == "/calendar":
            tool = self.tools["calendar"]
            result = tool.run(action="today")
            events = result.get("events", [])
            date = result.get("date", "today")
            if not events:
                return f"📅 No events scheduled for {date}."
            lines = [f"📅 **Today's Events ({date}):**"]
            for e in events:
                lines.append(f"  {e['time']} — {e['title']} ({e['duration_minutes']}min)")
            return "\n".join(lines)

        elif cmd.startswith("/model"):
            parts = user_input.strip().split()
            if len(parts) == 1:
                return f"🤖 Current model: `{self.llm.model}`"
            model_name = parts[1]
            self.llm.switch_model(model_name)
            return f"🤖 Switched to model: `{self.llm.model}`"

        elif cmd in ("/exit", "/quit"):
            return "__EXIT__"

        return None  # Not a special command

    def _execute_tool(self, tool_name: str, tool_args: Dict) -> str:
        """Execute a tool and return result as string."""
        if tool_name not in self.tools:
            return json.dumps({"success": False, "error": f"Unknown tool: {tool_name}"})

        tool = self.tools[tool_name]
        if self.verbose:
            print(f"\n  🔧 Calling tool: {tool_name}({json.dumps(tool_args, indent=2)})")

        try:
            result = tool.run(**tool_args)
        except TypeError as e:
            result = {"success": False, "error": f"Invalid tool arguments: {e}"}
        except Exception as e:
            result = {"success": False, "error": str(e)}

        result_str = json.dumps(result, indent=2, default=str)
        if self.verbose:
            print(f"  📤 Tool result: {result_str[:500]}...")
        return result_str

    def chat(self, user_input: str) -> str:
        """Process a user message and return the agent's response."""
        # Check for special commands
        special_response = self.handle_special_command(user_input)
        if special_response is not None:
            return special_response

        # Add user message to history
        self.memory.add_message("user", user_input)

        # Agentic loop: LLM → tool calls → LLM → ... → final response
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            messages = self.memory.get_messages_for_api()

            # Call LLM
            response = self.llm.chat(messages, tools=self.tool_schemas)

            if "error" in response:
                error_msg = f"❌ LLM Error: {response['error']}"
                self.memory.add_message("assistant", error_msg)
                return error_msg

            # Check for tool calls
            tool_calls = self.llm.extract_tool_calls(response)
            reply_text = self.llm.extract_reply(response)

            if tool_calls:
                # Add assistant message with tool calls to history
                choices = response.get("choices", [{}])
                assistant_msg = choices[0].get("message", {}) if choices else {}
                self.memory.messages.append({
                    "role": "assistant",
                    "content": assistant_msg.get("content") or "",
                    "tool_calls": tool_calls,
                    "timestamp": "tool_call",
                })

                # Execute each tool call
                for tc in tool_calls:
                    tool_name = tc.get("function", {}).get("name", "")
                    tool_args_str = tc.get("function", {}).get("arguments", "{}")
                    tool_call_id = tc.get("id", "call_0")

                    try:
                        tool_args = json.loads(tool_args_str) if isinstance(tool_args_str, str) else tool_args_str
                    except json.JSONDecodeError:
                        tool_args = {}

                    tool_result = self._execute_tool(tool_name, tool_args)

                    # Add tool result to history
                    self.memory.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "name": tool_name,
                        "content": tool_result,
                        "timestamp": "tool_result",
                    })

                # Continue loop to get final response
                continue

            # If we got here with no tool calls and no reply, break to avoid infinite loop
            if not reply_text and not tool_calls:
                break

            else:
                # No tool calls — this is the final response
                if reply_text:
                    self.memory.add_message("assistant", reply_text)
                    return reply_text
                else:
                    fallback = "I processed your request but have no additional response."
                    self.memory.add_message("assistant", fallback)
                    return fallback

        return "⚠️ Max iterations reached. The task may be too complex for a single turn."
