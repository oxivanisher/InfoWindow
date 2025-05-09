from mod_utils import mod_google_auth
from googleapiclient.discovery import build
from datetime import datetime, timedelta, date
import logging

today = date.today()
tomorrow = date.today() + timedelta(days=1)

class ToDo:
    def __init__(self, options):
        # This module authenticates from Google Auth API. We pull in the auth module 
        # wrapper to keep it clean. 
        logging.debug("Initializing Module: ToDo: Google")
        self.enabled = options["todo_google"]["enabled"]
        if self.enabled:
            ga = mod_google_auth.GoogleAuth()
            self.creds = ga.login()

    def list(self):
        if not self.enabled:
            logging.debug("Todo: Google not enabled")
            return []

        service = build('tasks', 'v1', credentials=self.creds)

        tasks_with_due = []
        items_with_due = []
        items_without_due = []

        # Fetch Results from all lists where todo is in the name
        tasklists = service.tasklists().list().execute()
        for tasklist in tasklists['items']:
            if "todo" in tasklist['title'].lower():
                results = service.tasks().list(tasklist=tasklist['id']).execute()

                if 'items' in list(results.keys()):
                    for task in results['items']:
                        if 'due' in list(task.keys()):
                            tasks_with_due.append(task)
                        else:
                            items_without_due.append({
                                "content": task['title'],
                                "priority": int(task['position']),
                                "today": False
                            })

        for task in sorted(tasks_with_due, key=lambda x: x['due']):
            is_today = False
            due = datetime.fromisoformat(task['due'].replace("Z", "+00:00")).date()
            if due < today:
                is_today = True
                task['title'] = f"Overdue: {task['title']}"
                task['position'] = 1
            elif due == today:
                is_today = True
            elif due == tomorrow:
                pass
            else:
                continue

            items_with_due.append({
                "content": task['title'],
                "priority": int(task['position']),
                "today": is_today
            })

        # Return results to main program
        return items_with_due + items_without_due
