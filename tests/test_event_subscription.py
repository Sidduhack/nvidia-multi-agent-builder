from uuid import uuid4

import pytest

from app.events.bus import EventBus, ProjectEvent


@pytest.mark.asyncio
async def test_wildcard_event_subscriber_receives_status_event() -> None:
    received = []

    async def handler(event: ProjectEvent) -> None:
        received.append(event.type)

    bus = EventBus()
    bus.subscribe("*", handler)
    await bus.publish(ProjectEvent(project_id=uuid4(), type="AGENT_STARTED"))
    assert received == ["AGENT_STARTED"]
