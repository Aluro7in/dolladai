#!/usr/bin/env python3
"""
DolladAI — Web Server v2.1
Flask-based web interface with file upload, voice, enhanced search,
and multi-provider API key management.
"""

import os
import sys
import json
import base64
import hashlib
import threading
import mimetypes
import tempfile
from pathlib import Path
from typing import Dict, Optional
from flask import Flask, render_template, request, jsonify, Response, session
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent_core import AIAgent
from llm_client import PROVIDERS, UniversalLLMClient

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max upload
app.secret_key = os.environ.get("FLASK_SECRET", os.urandom(32))
CORS(app)

_agent_lock = threading.Lock()
_agents: dict = {}

UPLOAD_DIR = os.path.expanduser("~/.ai_agent/uploads")
KEYS_DIR   = os.path.expanduser("~/.ai_agent")
KEYS_FILE  = os.path.join(KEYS_DIR, "user_providers.json")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(KEYS_DIR,   exist_ok=True)


# ── Secure key storage helpers ───────────────────────────────────────────────
def _mask_key(key: str) -> str:
    """Return a masked version for display: first 6 + *** + last 4."""
    if not key or len(key) < 12:
        return "***"
    return key[:6] + "•" * (len(key) - 10) + key[-4:]


def _load_user_providers() -> Dict:
    """Load saved provider configs (keys stored only in server memory / file)."""
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_user_providers(data: Dict):
    """Persist provider configs to disk (chmod 600)."""
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    try:
        os.chmod(KEYS_FILE, 0o600)
    except Exception:
        pass


# In-memory provider config per session: session_id → {provider, api_key, model, base_url}
_session_providers: Dict[str, Dict] = {}
_session_lock = threading.Lock()


def get_session_provider(session_id: str) -> Optional[Dict]:
    with _session_lock:
        return _session_providers.get(session_id)


def set_session_provider(session_id: str, config: Dict):
    with _session_lock:
        _session_providers[session_id] = config


def get_agent(session_id: str = "default", model: str = "default") -> AIAgent:
    with _agent_lock:
        if session_id not in _agents:
            agent = AIAgent(model=model)
            # Apply any saved provider config for this session
            pconf = get_session_provider(session_id)
            if pconf:
                agent.llm.switch_provider(
                    provider  = pconf.get("provider", "blackbox"),
                    api_key   = pconf.get("api_key", ""),
                    model     = pconf.get("model", "default"),
                    base_url  = pconf.get("base_url", ""),
                )
            _agents[session_id] = agent
        return _agents[session_id]


def extract_file_content(filepath: str, filename: str, mimetype: str) -> str:
    """Extract text content from uploaded files."""
    ext = Path(filename).suffix.lower()
    content_parts = []

    try:
        # PDF
        if ext == ".pdf" or "pdf" in mimetype:
            try:
                import PyPDF2
                with open(filepath, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages[:20]:  # max 20 pages
                        text += page.extract_text() or ""
                content_parts.append(f"[PDF Content — {len(reader.pages)} pages]\n{text[:8000]}")
            except Exception as e:
                content_parts.append(f"[PDF — could not extract text: {e}]")

        # Word documents
        elif ext in (".docx", ".doc"):
            try:
                from docx import Document
                doc = Document(filepath)
                text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                content_parts.append(f"[Word Document]\n{text[:8000]}")
            except Exception as e:
                content_parts.append(f"[Word doc — could not extract: {e}]")

        # Excel / CSV
        elif ext in (".xlsx", ".xls"):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
                rows = []
                for sheet in wb.sheetnames[:3]:
                    ws = wb[sheet]
                    rows.append(f"Sheet: {sheet}")
                    for row in list(ws.iter_rows(values_only=True))[:50]:
                        rows.append("\t".join(str(c) if c is not None else "" for c in row))
                content_parts.append(f"[Excel Spreadsheet]\n" + "\n".join(rows)[:6000])
            except Exception as e:
                content_parts.append(f"[Excel — could not extract: {e}]")

        elif ext == ".csv":
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                text = f.read(6000)
            content_parts.append(f"[CSV Data]\n{text}")

        # Images
        elif ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp") or "image" in mimetype:
            try:
                from PIL import Image
                img = Image.open(filepath)
                w, h = img.size
                mode = img.mode
                content_parts.append(
                    f"[Image: {filename}]\n"
                    f"Size: {w}×{h}px | Mode: {mode} | Format: {img.format}\n"
                    f"(Image uploaded — describe or analyze this image)"
                )
                # Also encode as base64 for vision models
                with open(filepath, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                content_parts.append(f"[IMAGE_BASE64:{b64[:100]}...]")  # truncated for context
            except Exception as e:
                content_parts.append(f"[Image: {filename} — {e}]")

        # Audio
        elif ext in (".mp3", ".wav", ".ogg", ".m4a", ".webm") or "audio" in mimetype:
            size_kb = os.path.getsize(filepath) // 1024
            content_parts.append(f"[Audio file: {filename}, {size_kb}KB — transcription not available in this mode]")

        # Plain text / code
        elif ext in (".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json",
                     ".yaml", ".yml", ".xml", ".sh", ".sql", ".rs", ".go", ".java",
                     ".cpp", ".c", ".h", ".rb", ".php", ".swift", ".kt") or "text" in mimetype:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                text = f.read(10000)
            content_parts.append(f"[{ext.upper()} File: {filename}]\n{text}")

        else:
            size_kb = os.path.getsize(filepath) // 1024
            content_parts.append(f"[File: {filename}, {size_kb}KB, type: {mimetype}]")

    except Exception as e:
        content_parts.append(f"[Error reading {filename}: {e}]")

    return "\n\n".join(content_parts)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True, silent=True) or {}
    message = (data.get("message") or "").strip()
    model = data.get("model", "default")
    session_id = data.get("session_id", "default")
    file_contexts = data.get("file_contexts", [])  # pre-extracted file content

    if not message and not file_contexts:
        return jsonify({"error": "Empty message"}), 400

    # Build full message with file context
    full_message = message
    if file_contexts:
        ctx_parts = []
        for fc in file_contexts:
            ctx_parts.append(f"--- Uploaded File: {fc.get('name', 'file')} ---\n{fc.get('content', '')}")
        full_message = "\n\n".join(ctx_parts) + "\n\n" + (message or "Analyze the uploaded file(s) above.")

    agent = get_agent(session_id, model)

    original_execute = agent._execute_tool
    tools_used = []

    def tracked_execute(tool_name, tool_args):
        tools_used.append(tool_name)
        return original_execute(tool_name, tool_args)

    agent._execute_tool = tracked_execute

    try:
        response = agent.chat(full_message)
    except Exception as e:
        response = f"❌ Agent error: {str(e)}"
    finally:
        agent._execute_tool = original_execute

    if response == "__EXIT__":
        response = "👋 Goodbye! Your data is saved. Refresh to start a new session."

    return jsonify({
        "response": response,
        "tools_used": list(dict.fromkeys(tools_used)),
        "model": agent.llm.model,
    })


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Handle file uploads — extract content and return it."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    filename = file.filename
    mimetype = file.mimetype or mimetypes.guess_type(filename)[0] or "application/octet-stream"

    # Save to temp location
    ext = Path(filename).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=UPLOAD_DIR) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        content = extract_file_content(tmp_path, filename, mimetype)
        size_kb = os.path.getsize(tmp_path) // 1024

        # For images, also return base64 preview
        preview_b64 = None
        if "image" in mimetype or ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
            try:
                with open(tmp_path, "rb") as f:
                    preview_b64 = f"data:{mimetype};base64," + base64.b64encode(f.read()).decode()
            except Exception:
                pass

        return jsonify({
            "success": True,
            "filename": filename,
            "mimetype": mimetype,
            "size_kb": size_kb,
            "content": content,
            "preview": preview_b64,
        })
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@app.route("/api/search", methods=["POST"])
def web_search():
    """Direct web search endpoint."""
    data = request.get_json(force=True, silent=True) or {}
    query = (data.get("query") or "").strip()
    search_type = data.get("type", "search")  # search | wikipedia | news
    session_id = data.get("session_id", "default")

    if not query:
        return jsonify({"error": "Empty query"}), 400

    agent = get_agent(session_id)
    result = agent.tools["web_search"].run(action=search_type, query=query, max_results=8)
    return jsonify(result)


@app.route("/api/model", methods=["POST"])
def switch_model():
    data = request.get_json(force=True, silent=True) or {}
    model = data.get("model", "default")
    session_id = data.get("session_id", "default")
    agent = get_agent(session_id)
    agent.llm.switch_model(model)
    return jsonify({"success": True, "model": agent.llm.model})


@app.route("/api/clear", methods=["POST"])
def clear_history():
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id", "default")
    agent = get_agent(session_id)
    agent.memory.clear()
    agent._init_system_message()
    return jsonify({"success": True, "message": "History cleared"})


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({"status": "ok", "name": "DolladAI", "version": "2.1.0", "sessions": len(_agents)})


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    session_id = request.args.get("session_id", "default")
    agent = get_agent(session_id)
    return jsonify(agent.tools["task_manager"].run(action="list"))


@app.route("/api/notes", methods=["GET"])
def get_notes():
    session_id = request.args.get("session_id", "default")
    agent = get_agent(session_id)
    return jsonify(agent.tools["note_manager"].run(action="list"))


@app.route("/api/calendar", methods=["GET"])
def get_calendar():
    session_id = request.args.get("session_id", "default")
    agent = get_agent(session_id)
    return jsonify(agent.tools["calendar"].run(action="today"))


# ── Provider / API Key Management ────────────────────────────────────────────

@app.route("/api/providers", methods=["GET"])
def list_providers():
    """Return all supported providers (no secrets)."""
    return jsonify({
        "providers": UniversalLLMClient.get_providers_info(),
        "default_provider": "blackbox",
    })


@app.route("/api/provider/set", methods=["POST"])
def set_provider():
    """
    Set a custom API provider + key for this session.
    The key is held in server memory only — never echoed back in full.
    """
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id", "default")
    provider   = (data.get("provider") or "blackbox").strip().lower()
    api_key    = (data.get("api_key") or "").strip()
    model      = (data.get("model") or "default").strip()
    base_url   = (data.get("base_url") or "").strip()
    save_key   = bool(data.get("save", False))  # persist to disk?

    # Validate provider
    if provider not in PROVIDERS and provider != "custom":
        return jsonify({"error": f"Unknown provider: {provider}"}), 400

    # Validate key is present (except ollama which can run without key)
    if provider != "ollama" and not api_key:
        return jsonify({"error": "API key is required"}), 400

    # Basic key format sanity (no spaces, reasonable length)
    if api_key and (" " in api_key or len(api_key) < 8):
        return jsonify({"error": "API key looks invalid (too short or contains spaces)"}), 400

    # Store in session memory
    pconf = {"provider": provider, "api_key": api_key, "model": model, "base_url": base_url}
    set_session_provider(session_id, pconf)

    # Apply to existing agent if already created
    with _agent_lock:
        if session_id in _agents:
            _agents[session_id].llm.switch_provider(
                provider=provider, api_key=api_key, model=model, base_url=base_url
            )
        else:
            # Will be applied on next get_agent call
            pass

    # Optionally persist (key saved to ~/.ai_agent/user_providers.json, chmod 600)
    if save_key:
        saved = _load_user_providers()
        saved[session_id] = {
            "provider": provider,
            "model":    model,
            "base_url": base_url,
            # Store key hash for verification, actual key in memory only
            "key_hash": hashlib.sha256(api_key.encode()).hexdigest()[:16],
            "key_masked": _mask_key(api_key),
        }
        _save_user_providers(saved)

    pname = PROVIDERS.get(provider, {}).get("name", provider)
    return jsonify({
        "success":    True,
        "provider":   provider,
        "provider_name": pname,
        "model":      model or PROVIDERS.get(provider, {}).get("default_model", ""),
        "key_masked": _mask_key(api_key),
        "message":    f"Now using {pname}" + (f" / {model}" if model and model != "default" else ""),
    })


@app.route("/api/provider/reset", methods=["POST"])
def reset_provider():
    """Reset to default Blackbox AI provider."""
    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id", "default")

    with _session_lock:
        _session_providers.pop(session_id, None)

    with _agent_lock:
        if session_id in _agents:
            _agents[session_id].llm.switch_provider(
                provider="blackbox",
                api_key=os.environ.get("BLACKBOX_API_KEY", ""),
                model="default",
            )

    return jsonify({"success": True, "message": "Reset to Blackbox AI (default)"})


@app.route("/api/provider/status", methods=["GET"])
def provider_status():
    """Return current provider info for a session (no key value)."""
    session_id = request.args.get("session_id", "default")
    pconf = get_session_provider(session_id)

    if pconf:
        provider = pconf.get("provider", "blackbox")
        pname    = PROVIDERS.get(provider, {}).get("name", provider)
        return jsonify({
            "using_custom": True,
            "provider":     provider,
            "provider_name": pname,
            "model":        pconf.get("model", ""),
            "key_masked":   _mask_key(pconf.get("api_key", "")),
            "has_base_url": bool(pconf.get("base_url")),
        })
    else:
        return jsonify({
            "using_custom":  False,
            "provider":      "blackbox",
            "provider_name": "Blackbox AI",
            "model":         "blackboxai/blackbox-pro",
            "key_masked":    _mask_key(os.environ.get("BLACKBOX_API_KEY", "")),
        })


@app.route("/api/provider/test", methods=["POST"])
def test_provider():
    """Quick connectivity test for a given provider + key."""
    data = request.get_json(force=True, silent=True) or {}
    provider = (data.get("provider") or "blackbox").strip().lower()
    api_key  = (data.get("api_key") or "").strip()
    model    = (data.get("model") or "default").strip()
    base_url = (data.get("base_url") or "").strip()

    if provider != "ollama" and not api_key:
        return jsonify({"success": False, "error": "API key required"}), 400

    client = UniversalLLMClient(
        model=model, provider=provider, api_key=api_key, base_url=base_url or None
    )
    result = client.chat([{"role": "user", "content": "Reply with exactly: OK"}])

    if "error" in result:
        return jsonify({"success": False, "error": result["error"]})

    reply = client.extract_reply(result)
    return jsonify({
        "success":  True,
        "reply":    reply[:200],
        "model":    client.model,
        "provider": provider,
        "message":  f"✅ Connection successful! Model: {client.model}",
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"""
╔══════════════════════════════════════════════════════╗
║       🤖  DolladAI v2.0  —  Starting Web Server      ║
╠══════════════════════════════════════════════════════╣
║  URL:    http://0.0.0.0:{port:<28}║
║  Upload: 50MB max (PDF, DOCX, images, code, CSV...)  ║
║  Voice:  Web Speech API (browser-native)             ║
╚══════════════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
