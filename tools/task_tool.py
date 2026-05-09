"""
Task Tool — manage a persistent to-do / task list stored as JSON.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional


TASKS_FILE = os.path.expanduser("~/.ai_agent/tasks.json")


def _load_tasks() -> List[Dict]:
    os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    return []


def _save_tasks(tasks: List[Dict]):
    os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


class TaskTool:
    name = "task_manager"
    description = "Manage a persistent task/to-do list: add, list, complete, delete, update tasks."

    SCHEMA = {
        "type": "function",
        "function": {
            "name": "task_manager",
            "description": "Manage your personal task list. Add, list, complete, delete, or update tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "list", "complete", "delete", "update", "clear_completed", "search"],
                        "description": "Action to perform.",
                    },
                    "title": {"type": "string", "description": "Task title."},
                    "description": {"type": "string", "description": "Task description or notes."},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Task priority."},
                    "due_date": {"type": "string", "description": "Due date (YYYY-MM-DD)."},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for the task."},
                    "task_id": {"type": "integer", "description": "Task ID (for complete/delete/update)."},
                    "query": {"type": "string", "description": "Search query (for search action)."},
                    "filter_status": {"type": "string", "enum": ["all", "pending", "completed"], "description": "Filter tasks by status."},
                },
                "required": ["action"],
            },
        },
    }

    def run(
        self,
        action: str,
        title: str = "",
        description: str = "",
        priority: str = "medium",
        due_date: str = "",
        tags: List[str] = None,
        task_id: int = None,
        query: str = "",
        filter_status: str = "all",
    ) -> Dict[str, Any]:
        tasks = _load_tasks()

        if action == "add":
            new_id = max((t["id"] for t in tasks), default=0) + 1
            task = {
                "id": new_id,
                "title": title,
                "description": description,
                "priority": priority,
                "due_date": due_date,
                "tags": tags or [],
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
            }
            tasks.append(task)
            _save_tasks(tasks)
            return {"success": True, "message": f"Task #{new_id} added: {title}", "task": task}

        elif action == "list":
            filtered = tasks
            if filter_status == "pending":
                filtered = [t for t in tasks if t["status"] == "pending"]
            elif filter_status == "completed":
                filtered = [t for t in tasks if t["status"] == "completed"]
            return {"success": True, "tasks": filtered, "count": len(filtered)}

        elif action == "complete":
            for t in tasks:
                if t["id"] == task_id:
                    t["status"] = "completed"
                    t["completed_at"] = datetime.now().isoformat()
                    _save_tasks(tasks)
                    return {"success": True, "message": f"Task #{task_id} marked complete."}
            return {"success": False, "error": f"Task #{task_id} not found."}

        elif action == "delete":
            original_len = len(tasks)
            tasks = [t for t in tasks if t["id"] != task_id]
            if len(tasks) < original_len:
                _save_tasks(tasks)
                return {"success": True, "message": f"Task #{task_id} deleted."}
            return {"success": False, "error": f"Task #{task_id} not found."}

        elif action == "update":
            for t in tasks:
                if t["id"] == task_id:
                    if title:
                        t["title"] = title
                    if description:
                        t["description"] = description
                    if priority:
                        t["priority"] = priority
                    if due_date:
                        t["due_date"] = due_date
                    if tags is not None:
                        t["tags"] = tags
                    _save_tasks(tasks)
                    return {"success": True, "message": f"Task #{task_id} updated.", "task": t}
            return {"success": False, "error": f"Task #{task_id} not found."}

        elif action == "clear_completed":
            before = len(tasks)
            tasks = [t for t in tasks if t["status"] != "completed"]
            _save_tasks(tasks)
            removed = before - len(tasks)
            return {"success": True, "message": f"Cleared {removed} completed tasks."}

        elif action == "search":
            results = [
                t for t in tasks
                if query.lower() in t["title"].lower()
                or query.lower() in t.get("description", "").lower()
                or any(query.lower() in tag.lower() for tag in t.get("tags", []))
            ]
            return {"success": True, "tasks": results, "count": len(results)}

        else:
            return {"success": False, "error": f"Unknown action: {action}"}
