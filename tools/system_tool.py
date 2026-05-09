"""
System Tool — get system info, environment variables, process management.
"""

import os
import sys
import platform
import subprocess
import psutil
from datetime import datetime
from typing import Dict, Any


class SystemTool:
    name = "system_info"
    description = "Get system information, manage environment variables, check processes, disk/memory usage."

    SCHEMA = {
        "type": "function",
        "function": {
            "name": "system_info",
            "description": "Get system info: CPU, memory, disk, processes, environment variables, OS details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "overview", "cpu", "memory", "disk", "processes",
                            "env_get", "env_set", "network", "uptime", "python_info"
                        ],
                        "description": "Action to perform.",
                    },
                    "env_key": {"type": "string", "description": "Environment variable name."},
                    "env_value": {"type": "string", "description": "Environment variable value (for env_set)."},
                    "process_name": {"type": "string", "description": "Process name filter."},
                },
                "required": ["action"],
            },
        },
    }

    def run(self, action: str, env_key: str = "", env_value: str = "", process_name: str = "") -> Dict[str, Any]:
        try:
            if action == "overview":
                return {
                    "success": True,
                    "os": platform.system(),
                    "os_version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "hostname": platform.node(),
                    "python_version": sys.version,
                    "cpu_count": os.cpu_count(),
                    "datetime": datetime.now().isoformat(),
                }

            elif action == "cpu":
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_freq = psutil.cpu_freq()
                return {
                    "success": True,
                    "cpu_percent": cpu_percent,
                    "cpu_count_logical": psutil.cpu_count(logical=True),
                    "cpu_count_physical": psutil.cpu_count(logical=False),
                    "frequency_mhz": cpu_freq.current if cpu_freq else None,
                }

            elif action == "memory":
                mem = psutil.virtual_memory()
                swap = psutil.swap_memory()
                return {
                    "success": True,
                    "total_gb": round(mem.total / 1e9, 2),
                    "available_gb": round(mem.available / 1e9, 2),
                    "used_gb": round(mem.used / 1e9, 2),
                    "percent_used": mem.percent,
                    "swap_total_gb": round(swap.total / 1e9, 2),
                    "swap_used_gb": round(swap.used / 1e9, 2),
                }

            elif action == "disk":
                partitions = []
                for part in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                        partitions.append({
                            "device": part.device,
                            "mountpoint": part.mountpoint,
                            "fstype": part.fstype,
                            "total_gb": round(usage.total / 1e9, 2),
                            "used_gb": round(usage.used / 1e9, 2),
                            "free_gb": round(usage.free / 1e9, 2),
                            "percent_used": usage.percent,
                        })
                    except Exception:
                        pass
                return {"success": True, "partitions": partitions}

            elif action == "processes":
                procs = []
                for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
                    try:
                        info = proc.info
                        if process_name and process_name.lower() not in info["name"].lower():
                            continue
                        procs.append(info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                procs.sort(key=lambda x: x.get("cpu_percent", 0) or 0, reverse=True)
                return {"success": True, "processes": procs[:50]}

            elif action == "env_get":
                if env_key:
                    return {"success": True, "key": env_key, "value": os.environ.get(env_key, None)}
                else:
                    safe_env = {k: v for k, v in os.environ.items() if "secret" not in k.lower() and "password" not in k.lower() and "token" not in k.lower()}
                    return {"success": True, "env": safe_env}

            elif action == "env_set":
                os.environ[env_key] = env_value
                return {"success": True, "message": f"Set {env_key}={env_value}"}

            elif action == "network":
                net = psutil.net_io_counters()
                addrs = {}
                for iface, addr_list in psutil.net_if_addrs().items():
                    addrs[iface] = [{"family": str(a.family), "address": a.address} for a in addr_list]
                return {
                    "success": True,
                    "bytes_sent_mb": round(net.bytes_sent / 1e6, 2),
                    "bytes_recv_mb": round(net.bytes_recv / 1e6, 2),
                    "interfaces": addrs,
                }

            elif action == "uptime":
                boot_time = psutil.boot_time()
                uptime_seconds = (datetime.now().timestamp() - boot_time)
                hours, rem = divmod(int(uptime_seconds), 3600)
                minutes, seconds = divmod(rem, 60)
                return {
                    "success": True,
                    "uptime": f"{hours}h {minutes}m {seconds}s",
                    "boot_time": datetime.fromtimestamp(boot_time).isoformat(),
                }

            elif action == "python_info":
                return {
                    "success": True,
                    "version": sys.version,
                    "executable": sys.executable,
                    "path": sys.path,
                    "platform": sys.platform,
                }

            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}
