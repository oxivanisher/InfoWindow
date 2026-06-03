from __future__ import annotations

import json
import logging
from pathlib import Path

from infowindow.utils.paths import PROJECT_ROOT

log = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.json"


def load_config(path: Path | None = None) -> dict:
    cfg_path = path or _DEFAULT_CONFIG_PATH
    log.info("Loading config from %s", cfg_path)
    with cfg_path.open() as fh:
        config = json.load(fh)

    general = config.get("general", {})

    # Propagate shared general settings into sub-sections that need them.
    for section in ("calendar_caldav", "calendar_google"):
        config.setdefault(section, {})
        config[section].setdefault("timezone", general.get("timezone", "UTC"))

    return config
