from __future__ import annotations

import logging
from datetime import datetime, timedelta, date

from googleapiclient.discovery import build

from infowindow.sources.types import TodoItem
from infowindow.utils.google_auth import GoogleAuth

log = logging.getLogger(__name__)


class ToDo:
    def __init__(self, config: dict) -> None:
        log.debug("Initializing Todo: Google")
        cfg = config["todo_google"]
        self.enabled: bool = cfg.get("enabled", False)
        if not self.enabled:
            return
        self._creds = GoogleAuth().login()

    def list(self) -> list[TodoItem]:
        if not self.enabled:
            log.debug("Todo: Google not enabled")
            return []

        today    = date.today()
        tomorrow = today + timedelta(days=1)
        service  = build("tasks", "v1", credentials=self._creds)

        with_due:    list[dict] = []
        without_due: list[TodoItem] = []

        tasklists = service.tasklists().list().execute()
        for tasklist in tasklists.get("items", []):
            if "todo" not in tasklist["title"].lower():
                continue
            results = service.tasks().list(tasklist=tasklist["id"]).execute()
            for task in results.get("items", []):
                if "due" in task:
                    with_due.append(task)
                else:
                    without_due.append(TodoItem(
                        content=task["title"],
                        priority=int(task["position"]),
                        today=False,
                    ))

        items: list[TodoItem] = []
        for task in sorted(with_due, key=lambda t: t["due"]):
            due_date = datetime.fromisoformat(task["due"].replace("Z", "+00:00")).date()
            if due_date < today:
                task["title"]    = f"Overdue: {task['title']}"
                task["position"] = "1"
                is_today = True
            elif due_date == today:
                is_today = True
            elif due_date == tomorrow:
                is_today = False
            else:
                continue
            items.append(TodoItem(
                content=task["title"],
                priority=int(task["position"]),
                today=is_today,
            ))

        return items + without_due
