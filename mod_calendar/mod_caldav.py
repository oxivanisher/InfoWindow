from caldav import DAVClient
from dateutil.parser import parse as dtparse
from datetime import datetime as dt, timedelta
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
        self.client = DAVClient(
            url=options["calendar_caldav"]["caldav_url"],
            username=options["calendar_caldav"]["username"],
            password=options["calendar_caldav"]["password"],
        )
        self.timeformat = options["timeformat"]
        self.additional = options["calendar_caldav"]["additional"]
        self.ignored = options["ignored"]
        self.sunday_first_dow = options["sunday_first_dow"]
        self.timezone = pytz.timezone(options["timezone"])

    def list(self):
        events = []
        items = []
        # now = dt.utcnow()
        now = dt.now(self.timezone)
        # now = dt.now()
        day_start_ts_now = dt.timestamp(now.replace(hour=0, minute=0, second=0, microsecond=0))
        #
        # today = dt.now(self.timezone).date()
        # midnight_today = self.timezone.localize(dt.combine(today, dt.min.time()))
        # last_second_tomorrow = self.timezone.localize(dt.combine(today + timedelta(days=1), dt.max.time()))
        # midnight_today_utc = midnight_today.astimezone(pytz.utc)
        # last_second_tomorrow_utc = last_second_tomorrow.astimezone(pytz.utc)

        # Fetch calendars
        principal = self.client.principal()
        calendars = principal.calendars()

        # Filter calendars
        logging.info(f"Available CalDAV calendars: {', '.join([x.name for x in calendars])}")
        selected_calendars = [
            cal for cal in calendars if cal.name in self.additional or not self.additional
        ]

        for calendar in selected_calendars:
            logging.debug(f"Fetching calendar: {calendar.name}")
            results = calendar.search(
                start=now, end=now + timedelta(days=30), event=True
            )
            logging.debug(f"Found {len(results)} results: {results}")

            for event in results:
                ical = event.icalendar_component
                logging.debug(f"Event: {event}")
                for comp in ical.walk():
                    if comp.name != "VEVENT":
                        continue

                    summary = comp.get("SUMMARY", "No Title")
                    if summary in self.ignored:
                        continue
                    # replace birthday emoji with ascii
                    summary = summary.replace("🎂", "[_i_]")
                    summary = replace_birth_year_with_age(summary)

                    start = comp.get("DTSTART").dt
                    if isinstance(start, dt):  # Ensure it's datetime, not date
                        start_str = start.isoformat()
                    else:
                        start = dt.combine(start, dt.min.time())
                        start_str = start.isoformat()

                    events.append((start_str, summary))

        # Sort events by start date
        events.sort()

        for start_str, summary in events:
            start = dtparse(start_str)
            today = start.date() <= dt.today().date() # oxi orig
            # today = start.date() == dt.today().date() # chatgpt 1

            # event_end = comp.get("DTEND")
            # if event_end:
            #     end = event_end.dt
            #     if isinstance(end, dt):  # Ensure it's a datetime object
            #         if end.tzinfo is None:  # If naive, localize it
            #             end = self.timezone.localize(end)  # <-- This fixes the issue
            #         else:
            #             end = end.astimezone(self.timezone)
            #     else:  # If it's a date, set it to the end of that day
            #         end = dt.combine(end, dt.max.time())
            #         end = self.timezone.localize(end)
            # else:
            #     end = start  # If no DTEND, assume it's a single-instance event
            #
            # now_local = dt.now(self.timezone)
            #
            # # Debugging output
            # print(f"DEBUG: end={end} (tzinfo={end.tzinfo}), now_local={now_local} (tzinfo={now_local.tzinfo})")
            #
            # if end < now_local:
            #     continue  # Skip past events

            if self.timeformat == "12h":
                st_date = start.strftime('%m-%d')
                st_time = start.strftime('%I:%M %p')
            else:
                st_date = start.strftime('%d.%m')
                st_time = start.strftime('%H:%M')

            if self.sunday_first_dow:
                week = start.strftime('%U')
            else:
                week = start.strftime('%W')

            event_start_ts_now = dt.timestamp(start.replace(hour=0, minute=0, second=0, microsecond=0))

            items.append({
                "date": st_date,
                "time": st_time,
                "content": summary,
                "today": today,
                "week": int(week),
                "start_ts": dt.timestamp(dtparse(start_str)),
                "days_away": (event_start_ts_now - day_start_ts_now) // 86400,  # days away
                "weeks_away": (event_start_ts_now - day_start_ts_now) // 604800  # weeks away
            })

        return items
