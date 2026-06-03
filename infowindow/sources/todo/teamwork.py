from __future__ import annotations

import base64
import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from infowindow.sources.types import TodoItem

log = logging.getLogger(__name__)

_PRIORITY_MAP = {"high": 1, "medium": 2, "low": 3, "none": 4}


class ToDo:
    def __init__(self, config: dict) -> None:
        log.debug("Initializing Todo: Teamwork")
        cfg = config.get("todo_teamwork", {})
        self.enabled: bool = cfg.get("enabled", False)
        if not self.enabled:
            return
        self._site = cfg["site"]
        token = base64.b64encode(f"{cfg['api_key']}:xxx".encode()).decode()
        self._auth_header = f"BASIC {token}"

    def list(self) -> list[TodoItem]:
        if not self.enabled:
            log.debug("Todo: Teamwork not enabled")
            return []

        url = f"https://{self._site}/tasks.json?sort=priority"
        req = urllib.request.Request(url, headers={"Authorization": self._auth_header})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())

        items: list[TodoItem] = []
        for task in data.get("todo-items", []):
            priority = _PRIORITY_MAP.get(str(task.get("priority", "")).lower(), 8)
            items.append(TodoItem(
                content=task["content"],
                priority=priority,
                today=False,
            ))
        return items
