from typing import Any

from messages.app.ports.event_publisher import EventPublisher


class RecordingPublisher(EventPublisher):
    def __init__(self):
        self.events: list[tuple[str, dict[str, Any]]] = []

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        self.events.append((event_type, payload))
