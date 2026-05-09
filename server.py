#!/usr/bin/env python3
"""
DolladAI — Web Server
Flask-based web interface for the AI agent.
Listens on port 3000.
"""

import os
import sys
import json
import threading
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_core import AIAgent

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Global agent instance (one per server, shared across requests)
# Each session gets its own via session_id in production; for simplicity use one global
_agent_lock = threading.Lock()
_agents: dict = {}  # session_id → AIAgent


def get_agent(session_id: str = "default", model: str = "default") -> AIAgent:
    """Get or create an agent for a session."""
    with _agent_lock:
        if session_id not in _agents:
            _agents[session_id] = AIAgent(model=model)
        return _agents[session_id]


@app.route("/")
def index():
    """Serve the main chat UI."""
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle a chat message."""
    data = request.get_json(force=True, silent=True) or {}
    message = (data.get("message") or "").strip()
    model = data.get("model", "default")
    session_id = data.get("session_id", "default")

    if not message:
        return jsonify({"error": "Empty message"}), 400

    agent = get_agent(session_id, model)

    # Track tool usage for the UI
    original_execute = agent._execute_tool
    tools_used = []

    def tracked_execute(tool_name, tool_args):
        tools_used.append(tool_name)
        return original_execute(tool_name, tool_args)

    agent._execute_tool = tracked_execute

    try:
        response = agent.chat(message)
    except Exception as e:
        response = f"❌ Agent error: {str(e)}"
    finally:
        agent._execute_tool = original_execute

    # Handle exit command
    if response == "__EXIT__":
        response = "👋 Goodbye! Your data is saved. Refresh to start a new session."

    return jsonify({
        "response": response,
        "tools_used": list(dict.fromkeys(tools_used)),  # deduplicated, ordered
        "model": agent.llm.model,
    })


@app.route("/api/model", methods=["POST"])
def switch_model():
    """Switch the LLM model for a session."""
    data = request.get_json(force=True, silent=True) or {}
    model = data.get("model", "default")
    session_id = data.get("session_id", "default")

    agent = get_agent(session_id)
    agent.llm.switch_model(model)

    return jsonify({"success": True, "model": agent.llm.model})


@app.route("/api/clear", methods=["POST"])
def clear_history():
    """Clear conversation history for a session."""
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id", "default")

    agent = get_agent(session_id)
    agent.memory.clear()
    agent._init_system_message()

    return jsonify({"success": True, "message": "History cleared"})


@app.route("/api/status", methods=["GET"])
def status():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "name": "DolladAI",
        "version": "1.0.0",
        "sessions": len(_agents),
    })


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    """Get all tasks."""
    session_id = request.args.get("session_id", "default")
    agent = get_agent(session_id)
    result = agent.tools["task_manager"].run(action="list")
    return jsonify(result)


@app.route("/api/notes", methods=["GET"])
def get_notes():
    """Get all notes."""
    session_id = request.args.get("session_id", "default")
    agent = get_agent(session_id)
    result = agent.tools["note_manager"].run(action="list")
    return jsonify(result)


@app.route("/api/calendar", methods=["GET"])
def get_calendar():
    """Get today's events."""
    session_id = request.args.get("session_id", "default")
    agent = get_agent(session_id)
    result = agent.tools["calendar"].run(action="today")
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"""
╔══════════════════════════════════════════════════════╗
║         🤖  DolladAI  —  Starting Web Server         ║
╠══════════════════════════════════════════════════════╣
║  URL:    http://0.0.0.0:{port:<28}║
║  Model:  Blackbox Pro (default)                      ║
║  Press Ctrl+C to stop                                ║
╚══════════════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
