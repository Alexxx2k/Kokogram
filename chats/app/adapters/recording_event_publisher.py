from chats.app.domain import ChatEvent


class RecordingEventPublisher:
    def __init__(self) -> None:
        self.events: list[ChatEvent] = []
        self.fail_with: Exception | None = None

    def set_failure(self, exc: Exception | None) -> None:
        self.fail_with = exc

    def clear(self) -> None:
        self.events.clear()
        self.fail_with = None

    def events_of_type(self, event_type: str) -> list[ChatEvent]:
        return [e for e in self.events if e.type == event_type]

    async def publish(self, event: ChatEvent) -> None:
        if self.fail_with is not None:
            raise self.fail_with
        self.events.append(event)
