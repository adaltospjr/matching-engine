from typing import Protocol

from matching_engine.engine.messages import Command, Event

class CommandSource(Protocol):
    async def get(self) -> Command | None:
        ...


class EventPublisher(Protocol):
    async def publish(self, event: Event) -> None:
        ...
