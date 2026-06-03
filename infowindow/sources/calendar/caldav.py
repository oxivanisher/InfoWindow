from __future__ import annotations

import logging
import re
from datetime import datetime as dt, timedelta, time, date

import pytz
from caldav import DAVClient
from dateutil.parser import parse as dtparse
from dateutil.rrule import rrulestr
from dateutil.tz import gettz

from infowindow.sources.types import CalendarItem

log = logging.getLogger(__name__)


def _replace_birth_year_with_age(summary: str) -> str:
    match = re.search(r"\((\d{4})\)", summary)
    if match:
        age = dt.now().year - int(match.group(1))
        summary = summary.replace(match.group(0), f"(Age {age})")
    return summary


class Cal:
    def __init__(self, config: dict) -> None:
        log.debug("Initializing Calendar: CalDAV")
        cfg = config["calendar_caldav"]
        self.enabled: bool = cfg.get("enabled", False)
        if not self.enabled:
            return
        self._client = DAVClient(
            url=cfg["caldav_url"],
            username=cfg["username"],
            password=cfg["password"],
            timeout=30,
        )
        self._timeformat: str  = config["general"]["timeformat"]
        self._additional: list = cfg.get("additional", [])
        self._ignored: list    = config["calendar"].get("ignored", [])
        self._sunday_first     = config["general"].get("sunday_first_dow", False)
        self._tz               = gettz(cfg.get("timezone", "UTC"))

    def list(self) -> list[CalendarItem]:
        if not self.enabled:
            log.debug("Calendar: CalDAV not enabled")
            return []

        now = dt.now(self._tz)
        principal  = self._client.principal()
        calendars  = principal.calendars()
        log.info("CalDAV calendars: %s", ", ".join(c.name for c in calendars))

        selected = [c for c in calendars if c.name in self._additional or not self._additional]
        events: list[tuple[str, str]] = []

        for cal in selected:
            log.debug("Fetching calendar: %s", cal.name)
            results = cal.search(
                start=now - timedelta(days=1),
                end=now + timedelta(days=60),
                event=True,
                expand=True,
            )
            for event in results:
                for comp in event.icalendar_instance.walk():
                    if comp.name != "VEVENT":
                        continue
                    summary = str(comp.get("SUMMARY", "No Title"))
                    if summary in self._ignored:
                        continue
                    summary = summary.replace("\U0001F382", "_i_")
                    summary = _replace_birth_year_with_age(summary)

                    start_orig = comp.get("DTSTART").dt
                    end_orig   = comp.get("DTEND", None)
                    rrule      = comp.get("RRULE")
                    is_all_day = not isinstance(start_orig, dt)

                    start = self._resolve_start(start_orig, end_orig, rrule, is_all_day, now)
                    if start is None:
                        continue
                    end = self._resolve_end(start, end_orig, is_all_day)
                    if end < now:
                        continue
                    events.append((start.isoformat(), summary))

        if not events:
            return []

        events.sort()
        now_local = dt.now(self._tz)
        items: list[CalendarItem] = []
        for start_str, summary in events:
            start    = dtparse(start_str)
            today    = start.date() <= now_local.date()
            days_away  = (start.date() - now_local.date()).days
            weeks_away = days_away // 7
            week = int(start.strftime("%U" if self._sunday_first else "%W"))
            st_date, st_time = self._format_datetime(start)
            items.append(CalendarItem(
                date=st_date, time=st_time, content=summary,
                today=today, week=week,
                start_ts=start.timestamp(),
                days_away=days_away, weeks_away=weeks_away,
            ))
        return items

    # ------------------------------------------------------------------
    def _resolve_start(self, start_orig, end_orig, rrule, is_all_day, now) -> dt | None:
        if rrule:
            rrule_str  = "RRULE:" + rrule.to_ical().decode()
            rule_start = (
                dt.combine(start_orig, time.min).replace(tzinfo=self._tz)
                if is_all_day else start_orig
            )
            occurrence = rrulestr(rrule_str, dtstart=rule_start).after(
                now.replace(hour=0, minute=0, second=0, microsecond=0), inc=True
            )
            if not occurrence:
                return None
            if isinstance(occurrence, date) and not isinstance(occurrence, dt):
                return dt.combine(occurrence, time.min).replace(tzinfo=self._tz)
            return (
                occurrence.replace(tzinfo=self._tz)
                if occurrence.tzinfo is None
                else occurrence.astimezone(self._tz)
            )

        if is_all_day:
            start = start_orig if isinstance(start_orig, dt) else dt.combine(start_orig, time.min).replace(tzinfo=self._tz)
        else:
            start = start_orig
            if start.tzinfo is None:
                start = pytz.utc.localize(start)
            start = start.astimezone(self._tz)
        return start

    def _resolve_end(self, start: dt, end_orig, is_all_day: bool) -> dt:
        if is_all_day:
            if end_orig:
                end_date = end_orig.dt if hasattr(end_orig, "dt") else end_orig
                return dt.combine(end_date, time.min).replace(tzinfo=self._tz) - timedelta(seconds=1)
            return start + timedelta(days=1)
        if end_orig:
            end = end_orig.dt if hasattr(end_orig, "dt") else end_orig
            if end.tzinfo is None:
                end = pytz.utc.localize(end)
            return end.astimezone(self._tz)
        return start + timedelta(hours=1)

    def _format_datetime(self, start: dt) -> tuple[str, str]:
        if self._timeformat == "12h":
            return start.strftime("%m-%d"), start.strftime("%I:%M %p")
        return start.strftime("%d.%m"), start.strftime("%H:%M")
