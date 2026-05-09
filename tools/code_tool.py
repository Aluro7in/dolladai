"""
Code Tool — execute Python code, run shell commands, install packages.
"""

import os
import sys
import subprocess
import tempfile
import traceback
from io import StringIO
from typing import Dict, Any


class CodeTool:
    name = "code_executor"
    description = "Execute Python code, run shell commands, install pip packages."

    SCHEMA = {
        "type": "function",
        "function": {
            "name": "code_executor",
            "description": "Execute Python code snippets or shell commands safely.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["run_python", "run_shell", "install_package", "run_script"],
                        "description": "Action to perform.",
                    },
                    "code": {"type": "string", "description": "Python code or shell command to execute."},
                    "package": {"type": "string", "description": "Package name to install (for install_package)."},
                    "script_path": {"type": "string", "description": "Path to script file (for run_script)."},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)."},
                    "working_dir": {"type": "string", "description": "Working directory for execution."},
                },
                "required": ["action"],
            },
        },
    }

    def run(
        self,
        action: str,
        code: str = "",
        package: str = "",
        script_path: str = "",
        timeout: int = 30,
        working_dir: str = "",
    ) -> Dict[str, Any]:
        cwd = working_dir or os.getcwd()

        try:
            if action == "run_python":
                return self._run_python(code, cwd, timeout)

            elif action == "run_shell":
                return self._run_shell(code, cwd, timeout)

            elif action == "install_package":
                return self._install_package(package, timeout)

            elif action == "run_script":
                if not os.path.exists(script_path):
                    return {"success": False, "error": f"Script not found: {script_path}"}
                ext = os.path.splitext(script_path)[1].lower()
                if ext == ".py":
                    cmd = [sys.executable, script_path]
                elif ext == ".sh":
                    cmd = ["bash", script_path]
                else:
                    cmd = [script_path]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd
                )
                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout[:10000],
                    "stderr": result.stderr[:5000],
                    "returncode": result.returncode,
                }

            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Execution timed out after {timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

    def _run_python(self, code: str, cwd: str, timeout: int) -> Dict[str, Any]:
        """Execute Python code in a subprocess for safety."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            tmp_path = f.name
        try:
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:10000],
                "stderr": result.stderr[:5000],
                "returncode": result.returncode,
            }
        finally:
            os.unlink(tmp_path)

    def _run_shell(self, command: str, cwd: str, timeout: int) -> Dict[str, Any]:
        """Execute a shell command."""
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout[:10000],
            "stderr": result.stderr[:5000],
            "returncode": result.returncode,
        }

    def _install_package(self, package: str, timeout: int) -> Dict[str, Any]:
        """Install a pip package."""
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package, "--quiet"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success": result.returncode == 0,
            "message": f"Package '{package}' {'installed' if result.returncode == 0 else 'failed to install'}",
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:2000],
        }
