"""
Calendar Tool — manage events/reminders stored as JSON.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List


CALENDAR_FILE = os.path.expanduser("~/.ai_agent/calendar.json")


def _load_events() -> List[Dict]:
    os.makedirs(os.path.dirname(CALENDAR_FILE), exist_ok=True)
    if os.path.exists(CALENDAR_FILE):
        with open(CALENDAR_FILE, "r") as f:
            return json.load(f)
    return []


def _save_events(events: List[Dict]):
    os.makedirs(os.path.dirname(CALENDAR_FILE), exist_ok=True)
    with open(CALENDAR_FILE, "w") as f:
        json.dump(events, f, indent=2)


class CalendarTool:
    name = "calendar"
    description = "Manage calendar events and reminders: add, list, delete, search events."

    SCHEMA = {
        "type": "function",
        "function": {
            "name": "calendar",
            "description": "Manage calendar events and reminders.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add_event", "list_events", "delete_event", "search_events", "upcoming", "today"],
                        "description": "Action to perform.",
                    },
                    "title": {"type": "string", "description": "Event title."},
                    "date": {"type": "string", "description": "Event date (YYYY-MM-DD)."},
                    "time": {"type": "string", "description": "Event time (HH:MM)."},
                    "duration_minutes": {"type": "integer", "description": "Duration in minutes."},
                    "description": {"type": "string", "description": "Event description."},
                    "reminder_minutes": {"type": "integer", "description": "Reminder before event (minutes)."},
                    "event_id": {"type": "integer", "description": "Event ID (for delete)."},
                    "query": {"type": "string", "description": "Search query."},
                    "days_ahead": {"type": "integer", "description": "Days ahead to look for upcoming events."},
                },
                "required": ["action"],
            },
        },
    }

    def run(
        self,
        action: str,
        title: str = "",
        date: str = "",
        time: str = "00:00",
        duration_minutes: int = 60,
        description: str = "",
        reminder_minutes: int = 15,
        event_id: int = None,
        query: str = "",
        days_ahead: int = 7,
    ) -> Dict[str, Any]:
        events = _load_events()

        if action == "add_event":
            new_id = max((e["id"] for e in events), default=0) + 1
            event = {
                "id": new_id,
                "title": title,
                "date": date,
                "time": time,
                "duration_minutes": duration_minutes,
                "description": description,
                "reminder_minutes": reminder_minutes,
                "created_at": datetime.now().isoformat(),
            }
            events.append(event)
            _save_events(events)
            return {"success": True, "message": f"Event #{new_id} added: {title} on {date} at {time}", "event": event}

        elif action == "list_events":
            events_sorted = sorted(events, key=lambda e: (e.get("date", ""), e.get("time", "")))
            return {"success": True, "events": events_sorted, "count": len(events_sorted)}

        elif action == "delete_event":
            original_len = len(events)
            events = [e for e in events if e["id"] != event_id]
            if len(events) < original_len:
                _save_events(events)
                return {"success": True, "message": f"Event #{event_id} deleted."}
            return {"success": False, "error": f"Event #{event_id} not found."}

        elif action == "search_events":
            results = [
                e for e in events
                if query.lower() in e.get("title", "").lower()
                or query.lower() in e.get("description", "").lower()
            ]
            return {"success": True, "events": results, "count": len(results)}

        elif action == "upcoming":
            today = datetime.now().date()
            end_date = today + timedelta(days=days_ahead)
            upcoming = []
            for e in events:
                try:
                    event_date = datetime.strptime(e["date"], "%Y-%m-%d").date()
                    if today <= event_date <= end_date:
                        upcoming.append(e)
                except Exception:
                    pass
            upcoming.sort(key=lambda e: (e.get("date", ""), e.get("time", "")))
            return {"success": True, "events": upcoming, "count": len(upcoming), "range": f"{today} to {end_date}"}

        elif action == "today":
            today_str = datetime.now().strftime("%Y-%m-%d")
            today_events = [e for e in events if e.get("date") == today_str]
            today_events.sort(key=lambda e: e.get("time", ""))
            return {"success": True, "events": today_events, "count": len(today_events), "date": today_str}

        else:
            return {"success": False, "error": f"Unknown action: {action}"}
