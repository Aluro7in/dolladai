# 🤖 DolladAI — Your Personal AI Agent

A fully-featured AI agent with a beautiful web UI, powered by the [Blackbox AI API](https://blackbox.ai). Manages your files, tasks, calendar, notes, runs code, searches the web, and remembers everything.

![DolladAI](https://img.shields.io/badge/DolladAI-v1.0.0-7c3aed?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-3776ab?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask)

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
| 🔍 **Web Search** | DuckDuckGo + Wikipedia search (no extra API key needed) |
| 🖥️ **System Monitor** | CPU, memory, disk, processes, environment variables |
| 🧠 **Memory** | Persistent conversation history + long-term memory |

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/Aluro7in/dolladai.git
cd dolladai
```

### 2. Set up your API key
```bash
cp .env.example .env
# Edit .env and add your Blackbox AI API key:
# BLACKBOX_API_KEY=your_key_here
```
Get your API key at → **https://blackbox.ai**

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the web server
```bash
python server.py
```
Open **http://localhost:3000** in your browser 🎉

---

## 🖥️ Web UI

The web interface runs on port 3000 and features:
- 💬 Real-time chat with markdown rendering
- 🔄 Model switcher (Blackbox Pro, Claude, Gemini, GPT-5, Kimi K2, Grok)
- 📋 Sidebar with capability shortcuts & quick actions
- ⚙️ Tool usage indicators
- 🧠 Persistent memory across sessions

---

## 💬 Example Prompts

```
Add a task: Review project proposal, high priority, due tomorrow
Search Wikipedia for quantum computing
Show my system info: CPU, memory, disk usage
Write and run Python code to generate a random password
Create a note titled "Ideas" with content: Build something amazing
Schedule a meeting tomorrow at 3pm for 1 hour
List all files in the current directory
/help
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

---

## 📁 Project Structure

```
├── server.py             # Flask web server (port 3000)
├── agent.py              # CLI entry point
├── agent_core.py         # Agent orchestrator (LLM + tools + memory)
├── llm_client.py         # Blackbox AI API client
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variable template
├── start.sh              # One-command startup script
├── templates/
│   └── index.html        # Web UI (dark theme chat interface)
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

## 🔑 Available Models

| Key | Model |
|---|---|
| `default` | Blackbox Pro (fast, capable) |
| `claude` | Claude Sonnet 4.6 |
| `gemini` | Gemini 3.1 Pro |
| `gpt4` | GPT-5.3 Codex |
| `deepseek` | Kimi K2.6 |
| `grok` | Grok Code Fast |

---

## 💾 Data Storage

All persistent data is stored locally in `~/.ai_agent/`:
- `tasks.json` — your task list
- `calendar.json` — your calendar events
- `notes.json` — your notes
- `long_term_memory.json` — remembered facts
- `conversation_history.json` — chat history

---

## 📄 License

MIT License — feel free to use, modify, and distribute.
