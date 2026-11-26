from typing import Any

from kokogram_shared import Clock, IdGenerator


class RecordingPublisher:
    def __init__(self, clock: Clock, id_generator: IdGenerator):
        self.events: list[dict[str, Any]] = []
        self.clock = clock
        self.id_generator = id_generator

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        envelope = {
            "event_id": str(self.id_generator.new_id()),
            "type": event_type,
            "occurred_at": self.clock.now().isoformat(),
            "payload": payload,
        }
        self.events.append(envelope)
