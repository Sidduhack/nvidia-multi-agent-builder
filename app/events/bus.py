from collections import defaultdict
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ProjectEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


EventHandler = Callable[[ProjectEvent], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self.history: list[ProjectEvent] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: ProjectEvent) -> None:
        self.history.append(event)
        for handler in self._handlers.get(event.type, []):
            await handler(event)
        for handler in self._handlers.get("*", []):
            await handler(event)
