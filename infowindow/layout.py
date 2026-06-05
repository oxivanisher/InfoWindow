"""Rendering functions — pure drawing logic, no network or hardware calls."""
from __future__ import annotations

import logging
import string
from typing import Any

from infowindow.display.canvas import Canvas
from infowindow.sources.types import CalendarItem, TodoItem, WeatherData

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_fetch(func, name: str) -> Any:
    try:
        return func()
    except Exception as exc:
        log.error("Failed to fetch %s, skipping: %s", name, exc, exc_info=True)
        return None


def _max_char_size(canvas: Canvas, chars: str, font: str) -> tuple[int, int]:
    max_w = max_h = 0
    for ch in chars:
        left, top, right, bottom = canvas.get_font(font).getbbox(ch)
        max_w = max(max_w, right - left)
        max_h = max(max_h, bottom - top)
    return max_w, max_h


def centered_text(
    canvas: Canvas,
    text: str,
    font: str,
    color: str,
    center_x: float,
    y: float,
) -> None:
    length = canvas.get_font(font).getlength(text)
    canvas.text(int(center_x - length / 2), y, text, font, color)


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def fetch_all(
    todo_sources: list,
    cal_sources: list,
    weather_source: Any,
) -> tuple[list[TodoItem], list[CalendarItem], WeatherData | None]:
    todo_items: list[TodoItem] = []
    for src in todo_sources:
        result = _safe_fetch(src.list, f"todo/{type(src).__name__}")
        if result:
            todo_items.extend(result)
    todo_items = sorted(todo_items, key=lambda x: (x["priority"] == 0, x["priority"]))

    cal_items: list[CalendarItem] = []
    for src in cal_sources:
        result = _safe_fetch(src.list, f"calendar/{type(src).__name__}")
        if result:
            cal_items.extend(result)
    cal_items = sorted(cal_items, key=lambda x: x["start_ts"])

    weather: WeatherData | None = None
    if weather_source is not None:
        weather = _safe_fetch(weather_source.list, "weather")

    return todo_items, cal_items, weather


# ---------------------------------------------------------------------------
# Static layout chrome
# ---------------------------------------------------------------------------

def draw_layout(canvas: Canvas) -> None:
    """Draw the static grid lines and coloured bands that frame the content."""
    w = canvas.width

    # Weather strip top dividers
    half = w / 2
    temp_rect_left  = half - 64
    temp_rect_right = half + 64
    canvas.line(335, 0, 335, 64, "black")
    canvas.rectangle(temp_rect_left, 0, temp_rect_right, 64, "red")
    canvas.line(465, 0, 465, 64, "black")

    # Centre column divider (between calendar and todo)
    canvas.line(392, 90, 392, 480, "black")
    canvas.rectangle(393, 64, 406, 480, "red")
    canvas.line(407, 90, 407, 480, "black")

    # Horizontal band separating weather strip from content
    canvas.line(0, 64, w, 64, "black")
    canvas.rectangle(0, 65, w, 90, "red")
    canvas.line(0, 91, w, 91, "black")


# ---------------------------------------------------------------------------
# Todo rendering
# ---------------------------------------------------------------------------

def measure_todos(canvas: Canvas, items: list[TodoItem], cell_spacing: int) -> int:
    """Return the pixel height needed for the todo header row + all items."""
    if not items:
        return 0
    font = "robotoBlack22"
    _, text_h = _max_char_size(canvas, string.printable, font)
    line_height = text_h + 2 * cell_spacing
    return (len(items) + 1) * (line_height + 2)  # +1 for header row


def render_todos(
    canvas: Canvas,
    items: list[TodoItem],
    cell_spacing: int,
    start_y: int = 92,
) -> int:
    """Draw todo header row + items; return y after the last rendered item."""
    if not items:
        return start_y

    font        = "robotoBlack22"
    _, text_h   = _max_char_size(canvas, string.printable, font)
    line_height = text_h + 2 * cell_spacing

    canvas.rectangle(408, start_y, 800, start_y + line_height, "red")
    centered_text(canvas, "TODO", font, "white", (408 + 800) / 2, start_y + cell_spacing)
    canvas.line(408, start_y + line_height + 1, 800, start_y + line_height + 1, "black")

    y = start_y + line_height + 2

    for item in items:
        if y + line_height + 2 > 480:
            break
        color = "red" if item.get("today") else "black"
        canvas.text(416, y + cell_spacing, item["content"].strip(), font, color)
        canvas.line(408, y + line_height + 1, 800, y + line_height + 1, "black")
        y += line_height + 2

    return y


# ---------------------------------------------------------------------------
# Calendar rendering
# ---------------------------------------------------------------------------

def render_calendar_column(
    canvas: Canvas,
    items: list[CalendarItem],
    x_min: int,
    x_max: int,
    opts: dict,
    cell_spacing: int,
    start_index: int = 0,
    max_y: int = 9999,
) -> tuple[int, int]:
    """Render calendar items into one column; return (last_index, next_y)."""
    date_font  = "robotoBlack14"
    entry_font = "robotoBlack22"

    _, digit_h        = _max_char_size(canvas, string.digits, date_font)
    sep_str           = ": pm" if opts.get("timeformat") == "12h" else "."
    l, t, r, b       = canvas.get_font(date_font).getbbox(sep_str)
    sep_w, sep_h      = r - l, b - t
    date_col_w        = sep_w + 4 * (canvas.get_font(date_font).getbbox("0")[2])
    date_h            = max(digit_h, sep_h)
    _, entry_h        = _max_char_size(canvas, string.printable, entry_font)
    line_height       = 2 * date_h + 2 * cell_spacing
    date_col_x        = x_min + date_col_w
    divider_x         = date_col_x + 2 * cell_spacing + 1

    y               = 92
    cur_days_away   = cur_weeks_away = cur_week = -1
    first           = True
    last_index      = start_index

    for cal_item in items[start_index:]:
        if y + line_height + 2 > max_y:  # respect hard ceiling (e.g. todo section)
            break

        new_week = False

        if cal_item["today"]:
            canvas.rectangle(
                x_min, y, x_max, y + line_height,
                opts.get("today_background_color", "white"),
            )

        font_color = opts.get("today_text_color", "black") if cal_item["today"] else "black"

        if cur_days_away  < 0: cur_days_away  = cal_item["days_away"]
        if cur_weeks_away < 0: cur_weeks_away = cal_item["weeks_away"]
        if cur_week       < 0: cur_week       = cal_item["week"]

        if not first:
            # Default: dashed line (same day)
            for x in range(x_min, x_max, 8):
                canvas.line(x, y, x + 3, y, "black")
                canvas.line(x + 4, y, x + 7, y, "white")
        first = False

        if cur_days_away != cal_item["days_away"]:
            cur_days_away = cal_item["days_away"]
            canvas.line(x_min, y, x_max, y, "black")

        if cur_week != cal_item["week"]:
            cur_week = cal_item["week"]
            new_week = True
            canvas.rectangle(x_min, y - 1, x_max, y, "black")

        if cur_weeks_away != cal_item["weeks_away"]:
            cur_weeks_away = cal_item["weeks_away"]
            if new_week:
                for x in range(x_min, x_max, 23):
                    canvas.rectangle(x,      y - 1, x + 11, y, "black")
                    canvas.rectangle(x + 12, y - 1, x + 23, y, "red")
            else:
                canvas.line(x_min, y, x_max, y, "red")

        # Bottom guard line (usually overridden by next iteration)
        canvas.line(x_min, y + line_height + 2, x_max, y + line_height + 2, "black")

        # Vertical separator between date col and content col
        canvas.line(divider_x, y, divider_x, y + line_height, "black")

        # Date and time
        canvas.text(x_min + cell_spacing, y,              cal_item["date"].strip(), date_font, font_color)
        canvas.text(x_min + cell_spacing, y + 1 + date_h, cal_item["time"].strip(), date_font, font_color)

        # Event text (truncated to fit)
        text_x   = divider_x + cell_spacing + 1
        max_w    = x_max - text_x - cell_spacing
        content  = canvas.truncate(cal_item["content"].strip(), entry_font, max_w)
        canvas.text(text_x, y + (line_height - entry_h) / 2, content, entry_font, font_color)

        last_index = items.index(cal_item)
        y += line_height + 2
        if y > 480:  # original overflow allowance — items may clip slightly at screen edge
            break

    return last_index, y


# ---------------------------------------------------------------------------
# Weather rendering
# ---------------------------------------------------------------------------

def render_weather(canvas: Canvas, data: WeatherData, config: dict) -> None:
    units  = config.get("weather", {}).get("units", "metric")
    u_speed, u_temp = {
        "imperial": ("mph",   "F"),
        "metric":   ("m/sec", "C"),
    }.get(units, ("m/sec", "K"))

    deg = "°"
    canvas.bitmap(2, 2, data["icon"])
    canvas.text(90,  2,  data["description"].title().strip(), "robotoBlack24", "black")
    canvas.text(90,  35, data["sunrise"],                     "robotoBlack18", "black")
    canvas.text(192, 35, data["sunset"],                      "robotoBlack18", "black")

    temp_str        = f"{data['temp_cur']}{deg}"
    l, t, r, b      = canvas.get_font("robotoBlack54").getbbox(temp_str)
    text_w          = r - l
    temp_x          = canvas.width / 2 - text_w / 2
    canvas.text(temp_x, 2, temp_str, "robotoBlack54", "white")
    canvas.text(temp_x + text_w - 18, 28, u_temp, "robotoBlack24", "white")

    canvas.bitmap(480, 0, "windSmall.bmp")
    canvas.text(520, 5,  data["wind"]["dir"],                       "robotoBlack18", "black")
    canvas.text(480, 35, f"{data['wind']['speed']}{u_speed}",       "robotoBlack18", "black")
    canvas.line(576, 0, 576, 64, "black")

    canvas.bitmap(616, 0, "rainSmall.bmp")
    canvas.text(601, 29, f"1hr: {data['rain']['1h']}",  "robotoBlack18", "black")
    canvas.text(601, 44, f"3hr: {data['rain']['3h']}",  "robotoBlack18", "black")
    canvas.line(687, 0, 687, 64, "black")

    canvas.bitmap(728, 0, "snowSmall.bmp")
    canvas.text(716, 29, f"1hr: {data['snow']['1h']}",  "robotoBlack18", "black")
    canvas.text(716, 44, f"3hr: {data['snow']['3h']}",  "robotoBlack18", "black")
