"""
File Tool — read, write, list, delete, move, copy files and directories.
"""

import os
import shutil
import glob as glob_module
from pathlib import Path
from typing import Dict, Any


class FileTool:
    name = "file_manager"
    description = "Manage files and directories: read, write, list, delete, move, copy, search."

    SCHEMA = {
        "type": "function",
        "function": {
            "name": "file_manager",
            "description": "Manage files and directories on the local filesystem.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["read", "write", "append", "list", "delete", "move", "copy", "exists", "mkdir", "search"],
                        "description": "Action to perform.",
                    },
                    "path": {"type": "string", "description": "File or directory path."},
                    "content": {"type": "string", "description": "Content to write (for write/append)."},
                    "destination": {"type": "string", "description": "Destination path (for move/copy)."},
                    "pattern": {"type": "string", "description": "Glob pattern or search term (for search/list)."},
                },
                "required": ["action", "path"],
            },
        },
    }

    def run(self, action: str, path: str, content: str = "", destination: str = "", pattern: str = "") -> Dict[str, Any]:
        path = os.path.expanduser(path)
        try:
            if action == "read":
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    data = f.read()
                return {"success": True, "content": data, "size": len(data)}

            elif action == "write":
                os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True, "message": f"Written {len(content)} chars to {path}"}

            elif action == "append":
                with open(path, "a", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True, "message": f"Appended to {path}"}

            elif action == "list":
                if pattern:
                    files = glob_module.glob(os.path.join(path, pattern), recursive=True)
                else:
                    files = os.listdir(path)
                return {"success": True, "files": sorted(files)}

            elif action == "delete":
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                return {"success": True, "message": f"Deleted {path}"}

            elif action == "move":
                shutil.move(path, destination)
                return {"success": True, "message": f"Moved {path} → {destination}"}

            elif action == "copy":
                if os.path.isdir(path):
                    shutil.copytree(path, destination)
                else:
                    shutil.copy2(path, destination)
                return {"success": True, "message": f"Copied {path} → {destination}"}

            elif action == "exists":
                return {"success": True, "exists": os.path.exists(path), "is_file": os.path.isfile(path), "is_dir": os.path.isdir(path)}

            elif action == "mkdir":
                os.makedirs(path, exist_ok=True)
                return {"success": True, "message": f"Directory created: {path}"}

            elif action == "search":
                results = []
                search_term = pattern or content
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    for fname in files:
                        fpath = os.path.join(root, fname)
                        try:
                            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                                text = f.read()
                            if search_term.lower() in text.lower():
                                results.append(fpath)
                        except Exception:
                            pass
                return {"success": True, "matches": results, "count": len(results)}

            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except FileNotFoundError:
            return {"success": False, "error": f"Path not found: {path}"}
        except PermissionError:
            return {"success": False, "error": f"Permission denied: {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
