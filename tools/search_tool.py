"""
Search Tool — web search via DuckDuckGo (no API key needed) and Wikipedia.
"""

import re
import json
import requests
from typing import Dict, Any, List
from urllib.parse import quote_plus


class SearchTool:
    name = "web_search"
    description = "Search the web using DuckDuckGo or Wikipedia. No API key required."

    SCHEMA = {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information using DuckDuckGo or Wikipedia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search", "wikipedia", "news"],
                        "description": "Search type: general web search, Wikipedia lookup, or news.",
                    },
                    "query": {"type": "string", "description": "Search query."},
                    "max_results": {"type": "integer", "description": "Maximum number of results (default 5)."},
                },
                "required": ["action", "query"],
            },
        },
    }

    HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AIAgent/1.0)"}

    def run(self, action: str, query: str, max_results: int = 5) -> Dict[str, Any]:
        try:
            if action == "search":
                return self._ddg_search(query, max_results)
            elif action == "wikipedia":
                return self._wikipedia(query)
            elif action == "news":
                return self._ddg_news(query, max_results)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _ddg_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Search DuckDuckGo Instant Answer API."""
        url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
        resp = requests.get(url, headers=self.HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []

        # Abstract
        if data.get("AbstractText"):
            results.append({
                "title": data.get("Heading", query),
                "snippet": data["AbstractText"],
                "url": data.get("AbstractURL", ""),
                "source": data.get("AbstractSource", ""),
            })

        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "")[:80],
                    "snippet": topic.get("Text", ""),
                    "url": topic.get("FirstURL", ""),
                    "source": "DuckDuckGo",
                })

        # Answer
        if data.get("Answer"):
            results.insert(0, {
                "title": "Direct Answer",
                "snippet": data["Answer"],
                "url": "",
                "source": data.get("AnswerType", "DuckDuckGo"),
            })

        if not results:
            # Fallback: HTML scrape
            return self._ddg_html_search(query, max_results)

        return {"success": True, "query": query, "results": results[:max_results]}

    def _ddg_html_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Fallback HTML search on DuckDuckGo."""
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        resp = requests.get(url, headers=self.HEADERS, timeout=15)
        resp.raise_for_status()

        results = []
        # Extract result snippets
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
        urls = re.findall(r'class="result__url"[^>]*>(.*?)</span>', resp.text, re.DOTALL)

        for i in range(min(max_results, len(titles))):
            results.append({
                "title": re.sub(r"<[^>]+>", "", titles[i]).strip() if i < len(titles) else "",
                "snippet": re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else "",
                "url": urls[i].strip() if i < len(urls) else "",
                "source": "DuckDuckGo",
            })

        return {"success": True, "query": query, "results": results}

    def _wikipedia(self, query: str) -> Dict[str, Any]:
        """Search Wikipedia."""
        search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote_plus(query)}"
        resp = requests.get(search_url, headers=self.HEADERS, timeout=15)

        if resp.status_code == 404:
            # Try search
            search_url2 = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote_plus(query)}&limit=5&format=json"
            resp2 = requests.get(search_url2, headers=self.HEADERS, timeout=15)
            data = resp2.json()
            return {
                "success": True,
                "query": query,
                "suggestions": data[1] if len(data) > 1 else [],
                "descriptions": data[2] if len(data) > 2 else [],
                "urls": data[3] if len(data) > 3 else [],
            }

        resp.raise_for_status()
        data = resp.json()
        return {
            "success": True,
            "title": data.get("title", ""),
            "summary": data.get("extract", ""),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "thumbnail": data.get("thumbnail", {}).get("source", "") if data.get("thumbnail") else "",
        }

    def _ddg_news(self, query: str, max_results: int) -> Dict[str, Any]:
        """Search DuckDuckGo news."""
        url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1"
        resp = requests.get(url, headers=self.HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        news = []
        for item in data.get("News", [])[:max_results]:
            news.append({
                "title": item.get("title", ""),
                "snippet": item.get("excerpt", ""),
                "url": item.get("url", ""),
                "date": item.get("date", ""),
                "source": item.get("source", ""),
            })

        if not news:
            return self._ddg_search(query + " news", max_results)

        return {"success": True, "query": query, "news": news}
