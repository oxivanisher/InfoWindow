from __future__ import annotations

import logging
import math
from datetime import datetime as dt

import requests

from infowindow.sources.types import WeatherData

log = logging.getLogger(__name__)

_DIRECTIONS = [
    (337.5, "N"), (292.5, "NW"), (247.5, "W"), (202.5, "SW"),
    (157.5, "S"), (122.5, "SE"), (67.5,  "E"), (22.5,  "NE"),
]


def _degrees_to_dir(deg: float) -> str:
    for threshold, label in _DIRECTIONS:
        if deg > threshold:
            return label
    return "N"


class Weather:
    _URL = "http://api.openweathermap.org/data/2.5/weather"

    def __init__(self, config: dict) -> None:
        log.debug("Initializing Weather: OpenWeatherMap")
        cfg = config["weather"]
        self._api_key   = cfg["api_key"]
        self._city      = cfg["city"]
        self._units     = cfg["units"]
        self._timeformat = config["general"]["timeformat"]

    def list(self) -> WeatherData:
        resp = requests.get(
            self._URL,
            params={"q": self._city, "units": self._units, "appid": self._api_key},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        fmt = "%I:%M %p" if self._timeformat == "12h" else "%H:%M"
        sunrise = dt.fromtimestamp(data["sys"]["sunrise"]).strftime(fmt)
        sunset  = dt.fromtimestamp(data["sys"]["sunset"]).strftime(fmt)

        def precip(key: str) -> dict[str, float]:
            return {"1h": data[key].get("1h", 0), "3h": data[key].get("3h", 0)} if key in data else {"1h": 0, "3h": 0}

        return WeatherData(
            description=data["weather"][0]["description"],
            humidity=data["main"]["humidity"],
            temp_cur=math.ceil(data["main"]["temp"]),
            temp_min=math.ceil(data["main"]["temp_min"]),
            temp_max=math.ceil(data["main"]["temp_max"]),
            sunrise=sunrise,
            sunset=sunset,
            rain=precip("rain"),
            snow=precip("snow"),
            wind={"dir": _degrees_to_dir(data["wind"]["deg"]), "speed": round(data["wind"]["speed"])},
            icon=f"{data['weather'][0]['icon']}.bmp",
        )
