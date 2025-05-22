from caldav import DAVClient
from dateutil.parser import parse as dtparse
from dateutil.tz import gettz
from datetime import datetime as dt, timedelta, time, date
from dateutil.rrule import rrulestr
import pytz
import re
import logging

# Disable excessive logging from caldav library
# logging.getLogger("caldav").setLevel(logging.WARNING)

def replace_birth_year_with_age(summary):
    match = re.search(r"\((\d{4})\)", summary)  # Find (YYYY)
    if match:
        birth_year = int(match.group(1))
        current_year = dt.now().year
        age = current_year - birth_year
        summary = summary.replace(f"({birth_year})", f"(Age {age})")  # Replace with age
    return summary

class Cal:
    def __init__(self, options):
        logging.debug("Initializing Module: Calendar: CalDAV")
        self.enabled = options["calendar_caldav"]["enabled"]
        if self.enabled:
            self.client = DAVClient(
                url=options["calendar_caldav"]["caldav_url"],
                username=options["calendar_caldav"]["username"],
                password=options["calendar_caldav"]["password"],
            )
            self.timeformat = options["timeformat"]
            self.additional = options["calendar_caldav"]["additional"]
            self.ignored = options["ignored"]
            self.sunday_first_dow = options["sunday_first_dow"]
            self.local_tz = gettz(options.get("calendar_caldav", {}).get("timezone", "Europe/Zurich"))

    def list(self):
        if not self.enabled:
            logging.debug("Calendar: CalDAV not enabled")
            return []

        events = []
        items = []
        now = dt.now(self.local_tz)

        # Fetch calendars
        principal = self.client.principal()
        calendars = principal.calendars()

        logging.info(f"Available CalDAV calendars: {', '.join([x.name for x in calendars])})")
        selected_calendars = [
            cal for cal in calendars if cal.name in self.additional or not self.additional
        ]

        for calendar in selected_calendars:
            logging.debug(f"Fetching calendar: {calendar.name}")
            results = calendar.search(start=now - timedelta(days=1), end=now + timedelta(days=60), event=True, expand=True)

            logging.debug(f"Found {len(results)} results")

            for event in results:
                ical = event.icalendar_instance

                for comp in ical.walk():
                    if comp.name != "VEVENT":
                        continue

                    summary = comp.get("SUMMARY", "No Title")
                    if summary in self.ignored:
                        continue

                    summary = summary.replace("\U0001F382", "_i_")
                    summary = replace_birth_year_with_age(summary)

                    start_orig = comp.get("DTSTART").dt
                    end_orig = comp.get("DTEND", None)
                    rrule = comp.get("RRULE")
                    is_all_day = not isinstance(start_orig, dt)

                    logging.debug(f"Raw DTSTART: {start_orig}, DTEND: {end_orig}, RRULE: {rrule}, is_all_day: {is_all_day}")

                    if rrule:
                        rrule_str = "RRULE:" + rrule.to_ical().decode()
                        rule_start = dt.combine(start_orig, time.min).replace(tzinfo=self.local_tz) if is_all_day else start_orig
                        rule = rrulestr(rrule_str, dtstart=rule_start)
                        next_occurrence = rule.after(now.replace(hour=0, minute=0, second=0, microsecond=0), inc=True)
                        if not next_occurrence:
                            logging.debug(f"No next occurrence found for recurring event: {summary}")
                            continue
                        if isinstance(next_occurrence, date) and not isinstance(next_occurrence, dt):
                            start = dt.combine(next_occurrence, time.min).replace(tzinfo=self.local_tz)
                        else:
                            if next_occurrence.tzinfo is None:
                                start = next_occurrence.replace(tzinfo=self.local_tz)
                            else:
                                start = next_occurrence.astimezone(self.local_tz)

                        if is_all_day:
                            end = start + timedelta(days=1) - timedelta(seconds=1)
                        else:
                            end = start + timedelta(hours=1)
                    else:
                        start = start_orig
                        if is_all_day:
                            start = start if isinstance(start, dt) else dt.combine(start, time.min).replace(tzinfo=self.local_tz)
                            if end_orig:
                                end_date = end_orig.dt if hasattr(end_orig, 'dt') else end_orig
                                end = dt.combine(end_date, time.min).replace(tzinfo=self.local_tz) - timedelta(seconds=1)
                            else:
                                end = start + timedelta(days=1)
                        else:
                            if start.tzinfo is None:
                                start = pytz.utc.localize(start)
                            start = start.astimezone(self.local_tz)

                            if end_orig:
                                end = end_orig.dt if hasattr(end_orig, 'dt') else end_orig
                                if end.tzinfo is None:
                                    end = pytz.utc.localize(end)
                                end = end.astimezone(self.local_tz)
                            else:
                                end = start + timedelta(hours=1)

                    if end < now:
                        logging.debug(f"Skipping event (in the past): {summary} (start: {start}, end: {end}, now: {now})")
                        continue

                    logging.debug(f"Adding event: {summary} at {start.isoformat()} (end: {end.isoformat()})")
                    events.append((start.isoformat(), summary))

        if not events:
            return []

        events.sort()
        items = []

        for start_str, summary in events:
            start = dtparse(start_str)
            now_local = dt.now(self.local_tz)
            logging.debug(f"Checking if today: event {summary} at {start}, now is {now_local}")
            if start.date() <= now_local.date():
                today = True
            else:
                today = False

            days_away = (start.date() - now_local.date()).days
            logging.debug(f"days_away: {days_away}")
            weeks_away = days_away // 7

            if self.timeformat == "12h":
                st_date = start.strftime('%m-%d')
                st_time = start.strftime('%I:%M %p')
            else:
                st_date = start.strftime('%d.%m')
                st_time = start.strftime('%H:%M')

            if self.sunday_first_dow:
                week = int(start.strftime('%U'))
            else:
                week = int(start.strftime('%W'))

            items.append({
                "summary": summary,
                "date": st_date,
                "time": st_time,
                "week": week,
                "start_ts": start.timestamp(),
                "today": today,
                "days_away": days_away,
                "weeks_away": weeks_away,
                "content": f"{summary}",
            })

        return items
