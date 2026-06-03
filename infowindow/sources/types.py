from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypedDict, runtime_checkable

if TYPE_CHECKING:
    from PIL import Image


class TodoItem(TypedDict):
    content: str
    priority: int
    today: bool


class CalendarItem(TypedDict):
    date: str
    time: str
    content: str
    today: bool
    week: int
    start_ts: float
    days_away: int
    weeks_away: int


class WindData(TypedDict):
    dir: str
    speed: int


class PrecipData(TypedDict):
    h1: float
    h3: float


class WeatherData(TypedDict):
    description: str
    humidity: int
    temp_cur: int
    temp_min: int
    temp_max: int
    sunrise: str
    sunset: str
    rain: dict[str, float]
    snow: dict[str, float]
    wind: WindData
    icon: str


@runtime_checkable
class TodoSource(Protocol):
    def list(self) -> list[TodoItem]: ...


@runtime_checkable
class CalendarSource(Protocol):
    def list(self) -> list[CalendarItem]: ...


@runtime_checkable
class WeatherSource(Protocol):
    def list(self) -> WeatherData: ...


@runtime_checkable
class DisplayDevice(Protocol):
    def init(self) -> None: ...
    def display(self, black_image: Image.Image, red_image: Image.Image) -> None: ...
    def sleep(self) -> None: ...
