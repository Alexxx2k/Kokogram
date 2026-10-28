from datetime import UTC, datetime, timedelta
from typing import Protocol


class Clock(Protocol):

    def now(self) -> datetime:
        ...


class SystemClock:

    def now(self) -> datetime:
        return datetime.now(UTC)


class FakeClock:

    def __init__(self, start: datetime | None = None) -> None:
        start = start or datetime(2026, 1, 1, tzinfo=UTC)
        if start.tzinfo is None:
            raise ValueError("FakeClock требует aware datetime (UTC)")
        self._now = start.astimezone(UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta | float) -> None:
        if not isinstance(delta, timedelta):
            delta = timedelta(seconds=delta)
        if delta < timedelta(0):
            raise ValueError("advance не двигает время назад; используйте set")
        self._now += delta

    def set(self, value: datetime) -> None:
        if value.tzinfo is None:
            raise ValueError("FakeClock требует aware datetime (UTC)")
        self._now = value.astimezone(UTC)
