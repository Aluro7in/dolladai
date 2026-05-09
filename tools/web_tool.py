"""
Web Tool — fetch URLs, scrape content, download files.
"""

import re
import os
import requests
from typing import Dict, Any
from urllib.parse import urlparse


class WebTool:
    name = "web_browser"
    description = "Fetch web pages, scrape content, download files from the internet."

    SCHEMA = {
        "type": "function",
        "function": {
            "name": "web_browser",
            "description": "Fetch web pages or download files from the internet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["fetch", "download", "get_links", "get_text"],
                        "description": "Action to perform.",
                    },
                    "url": {"type": "string", "description": "URL to fetch or download."},
                    "save_path": {"type": "string", "description": "Local path to save downloaded file."},
                    "headers": {"type": "object", "description": "Optional HTTP headers."},
                },
                "required": ["action", "url"],
            },
        },
    }

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (compatible; AIAgent/1.0)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def run(self, action: str, url: str, save_path: str = "", headers: dict = None) -> Dict[str, Any]:
        req_headers = {**self.HEADERS, **(headers or {})}
        try:
            if action == "fetch":
                resp = requests.get(url, headers=req_headers, timeout=30)
                resp.raise_for_status()
                return {
                    "success": True,
                    "status_code": resp.status_code,
                    "content": resp.text[:50000],  # cap at 50k chars
                    "content_type": resp.headers.get("Content-Type", ""),
                    "url": resp.url,
                }

            elif action == "get_text":
                resp = requests.get(url, headers=req_headers, timeout=30)
                resp.raise_for_status()
                # Strip HTML tags
                text = re.sub(r"<[^>]+>", " ", resp.text)
                text = re.sub(r"\s+", " ", text).strip()
                return {"success": True, "text": text[:20000], "url": resp.url}

            elif action == "get_links":
                resp = requests.get(url, headers=req_headers, timeout=30)
                resp.raise_for_status()
                links = re.findall(r'href=["\']([^"\']+)["\']', resp.text)
                base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                full_links = []
                for link in links:
                    if link.startswith("http"):
                        full_links.append(link)
                    elif link.startswith("/"):
                        full_links.append(base + link)
                return {"success": True, "links": list(set(full_links))[:100]}

            elif action == "download":
                resp = requests.get(url, headers=req_headers, timeout=60, stream=True)
                resp.raise_for_status()
                if not save_path:
                    fname = os.path.basename(urlparse(url).path) or "download"
                    save_path = os.path.join(os.getcwd(), fname)
                os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
                with open(save_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                size = os.path.getsize(save_path)
                return {"success": True, "saved_to": save_path, "size_bytes": size}

            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"HTTP Error: {e}"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection error."}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timed out."}
        except Exception as e:
            return {"success": False, "error": str(e)}
