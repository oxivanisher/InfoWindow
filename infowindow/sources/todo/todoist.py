from __future__ import annotations

import logging

from infowindow.sources.types import TodoItem

log = logging.getLogger(__name__)

# NOTE: The todoist-python package (v8 API) is unmaintained and the API has
# been discontinued. This module is kept as a stub. To restore Todoist
# support, migrate to todoist-api-python (REST API v2).


class ToDo:
    def __init__(self, config: dict) -> None:
        log.debug("Initializing Todo: Todoist (stub — v8 API is discontinued)")
        self.enabled = config.get("todo_todoist", {}).get("enabled", False)
        if self.enabled:
            log.warning(
                "Todoist backend is enabled but the underlying API is discontinued. "
                "Returning empty list. Migrate to todoist-api-python to restore support."
            )

    def list(self) -> list[TodoItem]:
        return []
