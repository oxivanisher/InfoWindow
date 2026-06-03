from __future__ import annotations

import logging
from datetime import datetime as dt, timezone

from dateutil.parser import parse as dtparse
from googleapiclient.discovery import build

from infowindow.sources.types import CalendarItem
from infowindow.utils.google_auth import GoogleAuth

log = logging.getLogger(__name__)
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)


class Cal:
    def __init__(self, config: dict) -> None:
        log.debug("Initializing Calendar: Google")
        cfg = config["calendar_google"]
        self.enabled: bool = cfg.get("enabled", False)
        if not self.enabled:
            return
        self._creds        = GoogleAuth().login()
        self._timeformat   = config["general"]["timeformat"]
        self._additional   = cfg.get("additional", [])
        self._ignored      = config["calendar"].get("ignored", [])
        self._sunday_first = config["general"].get("sunday_first_dow", False)

    def list(self) -> list[CalendarItem]:
        if not self.enabled:
            log.debug("Calendar: Google not enabled")
            return []

        service = build("calendar", "v3", credentials=self._creds)
        now_iso = dt.now(timezone.utc).isoformat()

        # Collect calendar IDs
        calendar_ids: list[str] = []
        page_token = None
        while True:
            resp = service.calendarList().list(pageToken=page_token).execute()
            for entry in resp["items"]:
                if entry.get("primary"):
                    calendar_ids.append(entry["id"])
                elif entry.get("summary") in self._additional:
                    calendar_ids.append(entry["id"])
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        # Fetch events, deduplicate by start time
        events: dict[str, dict] = {}
        for cal_id in calendar_ids:
            result = service.events().list(
                calendarId=cal_id, timeMin=now_iso,
                maxResults=30, singleEvents=True, orderBy="startTime",
            ).execute()
            for event in result.get("items", []):
                if event.get("summary") in self._ignored:
                    continue
                raw_start = event["start"].get("dateTime", event["start"].get("date"))
                key, counter = f"{raw_start}-0", 0
                while key in events:
                    counter += 1
                    key = f"{raw_start}-{counter}"
                events[key] = event

        today_str   = dt.today().strftime("%Y%m%d")
        day_start_ts = dt.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        items: list[CalendarItem] = []

        for key in sorted(events):
            event = events[key]
            raw_start = event["start"].get("dateTime", event["start"].get("date"))
            start     = dtparse(raw_start)

            today       = start.strftime("%Y%m%d") <= today_str
            st_date, st_time = self._format_datetime(start)
            week        = int(start.strftime("%U" if self._sunday_first else "%W"))
            event_day_ts = start.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()

            items.append(CalendarItem(
                date=st_date, time=st_time, content=event["summary"],
                today=today, week=week,
                start_ts=start.timestamp(),
                days_away=int((event_day_ts - day_start_ts) // 86400),
                weeks_away=int((event_day_ts - day_start_ts) // 604800),
            ))
        return items

    def _format_datetime(self, start: dt) -> tuple[str, str]:
        if self._timeformat == "12h":
            return start.strftime("%m-%d"), start.strftime("%I:%M %p")
        return start.strftime("%d.%m"), start.strftime("%H:%M")
