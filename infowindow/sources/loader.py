from __future__ import annotations

import importlib
import logging
from typing import Any

log = logging.getLogger(__name__)

# Registry maps config-section suffix → (module path, class name)
_TODO_BACKENDS: dict[str, tuple[str, str]] = {
    "google":   ("infowindow.sources.todo.google",   "ToDo"),
    "caldav":   ("infowindow.sources.todo.caldav",   "ToDo"),
    "todoist":  ("infowindow.sources.todo.todoist",  "ToDo"),
    "teamwork": ("infowindow.sources.todo.teamwork", "ToDo"),
}

_CALENDAR_BACKENDS: dict[str, tuple[str, str]] = {
    "google": ("infowindow.sources.calendar.google", "Cal"),
    "caldav": ("infowindow.sources.calendar.caldav", "Cal"),
}


def _load(registry: dict[str, tuple[str, str]], config: dict, prefix: str) -> list[Any]:
    sources = []
    for name, (module_path, cls_name) in registry.items():
        cfg_key = f"{prefix}_{name}"
        if not config.get(cfg_key, {}).get("enabled", False):
            continue
        try:
            mod = importlib.import_module(module_path)
            sources.append(getattr(mod, cls_name)(config))
            log.info("Loaded %s backend: %s", prefix, name)
        except ImportError:
            log.warning("Backend '%s/%s' not installed, skipping.", prefix, name)
        except Exception as exc:
            log.error("Failed to initialise %s/%s: %s", prefix, name, exc, exc_info=True)
    return sources


def load_todo_sources(config: dict) -> list:
    return _load(_TODO_BACKENDS, config, "todo")


def load_calendar_sources(config: dict) -> list:
    return _load(_CALENDAR_BACKENDS, config, "calendar")


def load_weather_source(config: dict):
    """Return a Weather instance if an api_key is configured, else None."""
    if config.get("weather", {}).get("api_key"):
        from infowindow.sources.weather.owm import Weather
        return Weather(config)
    log.warning("No weather api_key in config; weather disabled.")
    return None
