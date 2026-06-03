from __future__ import annotations

import logging
import pickle
import sys

from google.auth.transport.requests import Request
from google_auth_oauthlib import flow

from infowindow.utils.paths import PROJECT_ROOT

log = logging.getLogger(__name__)

_TOKEN_PATH   = PROJECT_ROOT / "token.pickle"
_SECRETS_PATH = PROJECT_ROOT / "google_secret.json"


def _is_cron() -> bool:
    return len(sys.argv) >= 2 and sys.argv[1] == "--cron"


class GoogleAuth:
    SCOPES = [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/tasks",
    ]

    def __init__(self) -> None:
        log.info("Initializing GoogleAuth")
        self._creds = None

    def login(self):
        if _TOKEN_PATH.exists():
            log.info("Loading token from %s", _TOKEN_PATH)
            with _TOKEN_PATH.open("rb") as fh:
                self._creds = pickle.load(fh)

        if not self._creds or not self._creds.valid:
            log.info("Credentials missing or invalid.")
            if self._creds and self._creds.expired and self._creds.refresh_token:
                log.info("Refreshing Google credentials.")
                self._creds.refresh(Request())
            else:
                if not _SECRETS_PATH.exists():
                    raise FileNotFoundError(f"Google secret not found: {_SECRETS_PATH}")
                if _is_cron():
                    raise RuntimeError(
                        "Google credentials require interactive login. "
                        "Run infowindow.py manually once to authenticate."
                    )
                app_flow = flow.InstalledAppFlow.from_client_secrets_file(
                    str(_SECRETS_PATH), self.SCOPES
                )
                app_flow.run_console()
                self._creds = app_flow.credentials

            log.info("Saving credentials to %s", _TOKEN_PATH)
            with _TOKEN_PATH.open("wb") as fh:
                pickle.dump(self._creds, fh)

        return self._creds
