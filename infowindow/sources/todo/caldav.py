from __future__ import annotations

import logging
from datetime import datetime, timedelta, date, UTC

from caldav import DAVClient

from infowindow.sources.types import TodoItem

log = logging.getLogger(__name__)

_today    = date.today()
_tomorrow = _today + timedelta(days=1)


class ToDo:
    def __init__(self, config: dict) -> None:
        log.debug("Initializing Todo: CalDAV")
        cfg = config["todo_caldav"]
        self.enabled: bool = cfg.get("enabled", False)
        if not self.enabled:
            return
        self._client = DAVClient(
            url=cfg["caldav_url"],
            username=cfg["username"],
            password=cfg["password"],
            timeout=30,
        )
        self._additional: list = cfg.get("additional", [])

    def list(self) -> list[TodoItem]:
        if not self.enabled:
            log.debug("Todo: CalDAV not enabled")
            return []

        today    = date.today()
        tomorrow = today + timedelta(days=1)
        now      = datetime.now(UTC)

        principal = self._client.principal()
        calendars = principal.calendars()
        log.info("CalDAV calendars for todo: %s", ", ".join(c.name for c in calendars))
        selected  = [c for c in calendars if c.name in self._additional or not self._additional]

        with_date:    list[tuple[str, object]] = []
        without_date: list[tuple[str, object]] = []

        for cal in selected:
            log.debug("Fetching todos from: %s", cal.name)
            results = cal.search(
                start=now - timedelta(days=360), end=now + timedelta(days=60),
                todo=True, expand=True,
            )
            for todo in results:
                for comp in todo.icalendar_instance.walk():
                    if comp.name != "VTODO":
                        continue
                    summary = str(comp.get("SUMMARY", "No Title"))
                    if "DUE" in comp:
                        due = comp.get("DUE").dt
                        if not isinstance(due, datetime):
                            due = datetime.combine(due, datetime.min.time())
                        with_date.append((due.isoformat(), comp))
                    elif "DTSTART" in comp:
                        start = comp.get("DTSTART").dt
                        if not isinstance(start, datetime):
                            start = datetime.combine(start, datetime.min.time())
                        with_date.append((start.isoformat(), comp))
                    else:
                        without_date.append((summary, comp))

        items: list[TodoItem] = []

        for _, comp in sorted(without_date):
            items.append(TodoItem(
                content=str(comp.get("SUMMARY", "No Title")),
                priority=int(comp.get("PRIORITY", 0)),
                today=False,
            ))

        for due_str, comp in sorted(with_date, key=lambda t: t[0]):
            due_date = datetime.fromisoformat(due_str.replace("Z", "+00:00")).date()
            if due_date < today:
                is_today = True
                comp["SUMMARY"] = f"Overdue: {comp['SUMMARY']}"
                comp["PRIORITY"] = 1
            elif due_date == today:
                is_today = True
            elif due_date == tomorrow:
                is_today = False
            else:
                continue
            items.append(TodoItem(
                content=str(comp.get("SUMMARY", "No Title")),
                priority=int(comp.get("PRIORITY", 0)),
                today=is_today,
            ))

        return items
