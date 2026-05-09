"""
Note Tool — create, read, search, and manage personal notes.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List


NOTES_FILE = os.path.expanduser("~/.ai_agent/notes.json")


def _load_notes() -> List[Dict]:
    os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r") as f:
            return json.load(f)
    return []


def _save_notes(notes: List[Dict]):
    os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)


class NoteTool:
    name = "note_manager"
    description = "Create, read, update, delete, and search personal notes."

    SCHEMA = {
        "type": "function",
        "function": {
            "name": "note_manager",
            "description": "Manage personal notes: create, read, update, delete, search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "read", "update", "delete", "list", "search"],
                        "description": "Action to perform.",
                    },
                    "title": {"type": "string", "description": "Note title."},
                    "content": {"type": "string", "description": "Note content."},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for the note."},
                    "note_id": {"type": "integer", "description": "Note ID (for read/update/delete)."},
                    "query": {"type": "string", "description": "Search query."},
                },
                "required": ["action"],
            },
        },
    }

    def run(
        self,
        action: str,
        title: str = "",
        content: str = "",
        tags: List[str] = None,
        note_id: int = None,
        query: str = "",
    ) -> Dict[str, Any]:
        notes = _load_notes()

        if action == "create":
            new_id = max((n["id"] for n in notes), default=0) + 1
            note = {
                "id": new_id,
                "title": title,
                "content": content,
                "tags": tags or [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            notes.append(note)
            _save_notes(notes)
            return {"success": True, "message": f"Note #{new_id} created: {title}", "note": note}

        elif action == "read":
            for n in notes:
                if n["id"] == note_id:
                    return {"success": True, "note": n}
            return {"success": False, "error": f"Note #{note_id} not found."}

        elif action == "update":
            for n in notes:
                if n["id"] == note_id:
                    if title:
                        n["title"] = title
                    if content:
                        n["content"] = content
                    if tags is not None:
                        n["tags"] = tags
                    n["updated_at"] = datetime.now().isoformat()
                    _save_notes(notes)
                    return {"success": True, "message": f"Note #{note_id} updated.", "note": n}
            return {"success": False, "error": f"Note #{note_id} not found."}

        elif action == "delete":
            original_len = len(notes)
            notes = [n for n in notes if n["id"] != note_id]
            if len(notes) < original_len:
                _save_notes(notes)
                return {"success": True, "message": f"Note #{note_id} deleted."}
            return {"success": False, "error": f"Note #{note_id} not found."}

        elif action == "list":
            notes_sorted = sorted(notes, key=lambda n: n.get("updated_at", ""), reverse=True)
            summaries = [{"id": n["id"], "title": n["title"], "tags": n["tags"], "updated_at": n["updated_at"]} for n in notes_sorted]
            return {"success": True, "notes": summaries, "count": len(summaries)}

        elif action == "search":
            results = [
                n for n in notes
                if query.lower() in n.get("title", "").lower()
                or query.lower() in n.get("content", "").lower()
                or any(query.lower() in tag.lower() for tag in n.get("tags", []))
            ]
            return {"success": True, "notes": results, "count": len(results)}

        else:
            return {"success": False, "error": f"Unknown action: {action}"}
