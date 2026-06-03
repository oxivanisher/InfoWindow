#!/usr/bin/env python3
"""InfoWindow — e-ink display updater."""
from __future__ import annotations

import logging
import os

from infowindow.config import load_config
from infowindow.display import get_display
from infowindow.display.canvas import Canvas
from infowindow.layout import (
    draw_layout,
    fetch_all,
    render_calendar_column,
    render_todos,
    render_weather,
    centered_text,
)
from infowindow.sources.loader import (
    load_calendar_sources,
    load_todo_sources,
    load_weather_source,
)

log = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%Y-%d-%m %H:%M:%S",
        level=logging.DEBUG if os.getenv("DEBUG") else logging.INFO,
    )

    config = load_config()
    general = config["general"]

    todo_sources    = load_todo_sources(config)
    cal_sources     = load_calendar_sources(config)
    weather_source  = load_weather_source(config)

    todo_items, cal_items, weather_data = fetch_all(todo_sources, cal_sources, weather_source)

    canvas = Canvas({"timeformat": general["timeformat"]})
    cell_spacing = general.get("cell_spacing", 2)

    draw_layout(canvas)

    todo_y = render_todos(canvas, todo_items, cell_spacing)

    cal_opts = {
        **config.get("calendar", {}),
        "timeformat": general["timeformat"],
    }

    last_item = render_calendar_column(canvas, cal_items, 0, 391, cal_opts, cell_spacing)

    if todo_y == 92:  # no tasks rendered — use right column for overflow calendar
        render_calendar_column(canvas, cal_items, 408, 800, cal_opts, cell_spacing, last_item + 1)
        left_title, right_title = "CALENDAR 1/2", "CALENDAR 2/2"
    else:
        left_title, right_title = "CALENDAR", "TODO"

    centered_text(canvas, left_title,  "robotoBlack24", "white", 200, 64)
    centered_text(canvas, right_title, "robotoBlack24", "white", 600, 64)

    if weather_data is not None:
        render_weather(canvas, weather_data, config)

    rotation = general.get("rotation", 0)
    black_img, red_img = canvas.render(rotation)

    device = get_display()
    device.display(black_img, red_img)
    device.sleep()


if __name__ == "__main__":
    main()
