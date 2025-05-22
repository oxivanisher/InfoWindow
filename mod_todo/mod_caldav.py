from caldav import DAVClient
from datetime import datetime, timedelta, date
import logging

today = date.today()
tomorrow = date.today() + timedelta(days=1)

class ToDo:
    def __init__(self, options):
        logging.debug("Initializing Module: ToDo: CalDAV")
        self.enabled = options["todo_caldav"]["enabled"]
        if self.enabled:
            self.client = DAVClient(
                url=options["todo_caldav"]["caldav_url"],
                username=options["todo_caldav"]["username"],
                password=options["todo_caldav"]["password"],
            )
            self.timeformat = options["timeformat"]
            self.additional = options["todo_caldav"]["additional"]
            # self.sunday_first_dow = options["sunday_first_dow"]

    def list(self):
        if not self.enabled:
            logging.debug("Todo: CalDAV not enabled")
            return []

        todos_without_date = []
        todos_with_date = []
        todos = []
        now = datetime.utcnow()

        # Fetch calendars
        principal = self.client.principal()
        calendars = principal.calendars()

        # Filter calendars
        logging.info(f"Available CalDAV calendars for todo: {', '.join([x.name for x in calendars])}")
        selected_calendars = [
            cal for cal in calendars if cal.name in self.additional or not self.additional
        ]

        for calendar in selected_calendars:
            logging.debug(f"Fetching todos from calendar: {calendar.name}")
            results = calendar.search(
                start=now - timedelta(days=30), end=now + timedelta(days=60), todo=True, expand=True
            )
            logging.debug(f"Found {len(results)} results: {results}")

            for todo in results:
                ical = todo.icalendar_component
                logging.debug(f"Todo URL: {todo}")
                for comp in ical.walk():
                    if comp.name != "VTODO":
                        continue

                    summary = comp.get("SUMMARY", "No Title")
                    if "DUE" in comp.keys():
                        logging.debug(f"Found {summary} with DUE")
                        due = comp.get("DUE").dt
                        if isinstance(due, datetime):  # Ensure it's datetime, not date
                            due_str = due.isoformat()
                        else:
                            due = datetime.combine(due, datetime.min.time())
                            due_str = due.isoformat()

                        logging.debug(f"Due {due_str}")
                        todos_with_date.append((due_str, comp))

                    elif "DTSTART" in comp.keys():
                        logging.debug(f"Found {summary} with DTSTART")
                        start = comp.get("DTSTART").dt
                        if isinstance(start, datetime):  # Ensure it's datetime, not date
                            start_str = start.isoformat()
                        else:
                            start = datetime.combine(start, datetime.min.time())
                            start_str = start.isoformat()

                        logging.debug(f"Start {start_str}")
                        todos_with_date.append((start_str, comp))

                    else:
                        todos_without_date.append((summary, comp))

        for summary, todo in sorted(todos_without_date):
            todos.append({"content": todo.get("SUMMARY", "No Title"),
                          "priority": todo.get("PRIORITY", 0),
                          "today": False
                          })

        for due_str, todo in sorted(todos_with_date, key=lambda tup: tup[0]):
            is_today = False
            due = datetime.fromisoformat(due_str.replace("Z", "+00:00")).date()
            if due < today:
                is_today = True
                todo['SUMMARY'] = f"Overdue: {todo['SUMMARY']}"
                todo['PRIORITY'] = 1
            elif due == today:
                is_today = True
            elif due == tomorrow:
                pass
            else:
                continue

            todos.append({"content": todo.get("SUMMARY", "No Title"),
                          "priority": todo.get("PRIORITY", 0),
                          "today": is_today
                          })

        return todos
