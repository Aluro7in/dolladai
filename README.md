# 🤖 AI Personal Agent — Powered by Blackbox AI

A fully-featured AI agent written in Python that manages **everything** using the Blackbox AI API.

---

## ✨ Features

| Capability | Description |
|---|---|
| 🗂️ **File Manager** | Read, write, list, search, move, copy files & directories |
| 🌐 **Web Browser** | Fetch pages, scrape content, download files |
| 💻 **Code Executor** | Run Python code, shell commands, install packages |
| ✅ **Task Manager** | Persistent to-do list with priorities, due dates, tags |
| 📅 **Calendar** | Schedule events, reminders, view upcoming events |
| 📝 **Notes** | Create, search, and manage personal notes |
| 🔍 **Web Search** | DuckDuckGo + Wikipedia search (no API key needed) |
| 💻 **System Monitor** | CPU, memory, disk, processes, environment variables |
| 🧠 **Memory** | Persistent conversation history + long-term memory |

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the agent
```bash
# Interactive mode (recommended)
python agent.py

# Single query mode
python agent.py -q "What files are in my home directory?"

# Use a specific model
python agent.py --model gpt4
python agent.py --model claude
python agent.py --model gemini
python agent.py --model deepseek

# Verbose mode (shows tool calls)
python agent.py --verbose
```

---

## 💬 Usage Examples

### File Management
```
You › Read the file /etc/hostname
You › List all Python files in /home/user/projects
You › Create a file called notes.txt with "Hello World"
You › Search for files containing "TODO" in /home/user
```

### Task Management
```
You › Add a task: Buy groceries, high priority, due tomorrow
You › Show all my pending tasks
You › Mark task #3 as complete
You › What tasks are due this week?
```

### Calendar
```
You › Schedule a meeting tomorrow at 2pm for 1 hour
You › What events do I have today?
You › Show upcoming events for the next 7 days
```

### Notes
```
You › Create a note titled "Ideas" with content "Build an AI agent"
You › Search my notes for "project"
You › Show all my notes
```

### Web Search
```
You › Search for the latest Python news
You › What is quantum computing? (Wikipedia)
You › Find news about AI developments
```

### Code Execution
```
You › Run this Python code: print(sum(range(100)))
You › Install the numpy package
You › Run the shell command: ls -la
```

### System Info
```
You › Show my system overview
You › How much memory am I using?
You › What processes are running?
You › Show disk usage
```

---

## 🛠️ Special Commands

| Command | Description |
|---|---|
| `/help` | Show all commands |
| `/remember <fact>` | Store a fact in long-term memory |
| `/recall [query]` | Recall stored memories |
| `/forget <query>` | Remove memories matching query |
| `/tasks` | Quick view of pending tasks |
| `/notes` | Quick view of all notes |
| `/calendar` | Today's events |
| `/model <name>` | Switch LLM model |
| `/clear` | Clear conversation history |
| `/history` | Show conversation stats |
| `/exit` | Exit the agent |

---

## 📁 Project Structure

```
├── agent.py              # Main entry point (CLI)
├── agent_core.py         # Agent orchestrator (LLM + tools + memory)
├── llm_client.py         # Blackbox AI API client
├── requirements.txt      # Python dependencies
├── tools/
│   ├── file_tool.py      # File system operations
│   ├── web_tool.py       # Web fetching & downloading
│   ├── code_tool.py      # Python & shell execution
│   ├── task_tool.py      # Task/to-do management
│   ├── system_tool.py    # System information
│   ├── calendar_tool.py  # Calendar & events
│   ├── note_tool.py      # Notes management
│   └── search_tool.py    # Web search (DuckDuckGo + Wikipedia)
└── memory/
    └── memory_manager.py # Conversation + long-term memory
```

---

## 💾 Data Storage

All persistent data is stored in `~/.ai_agent/`:
- `tasks.json` — your task list
- `calendar.json` — your calendar events
- `notes.json` — your notes
- `long_term_memory.json` — remembered facts
- `preferences.json` — user preferences
- `conversation_history.json` — chat history
- `.history` — readline input history

---

## 🔑 API Configuration

The agent uses the Blackbox AI API. The API key is pre-configured.

Available models:
- `default` — blackboxai (fast, capable)
- `gpt4` — GPT-4o
- `claude` — Claude Sonnet
- `gemini` — Gemini 2.0 Flash
- `deepseek` — DeepSeek V3

---

## 🔒 Security Notes

- Code execution runs in subprocesses for isolation
- Environment variable display filters out secrets/passwords/tokens
- All data is stored locally in your home directory
