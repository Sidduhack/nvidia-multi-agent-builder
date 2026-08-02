from collections import defaultdict
from typing import Any
from uuid import UUID


class ProjectMemory:
    """Small structured memory store for MVP; persistence comes in the database phase."""

    def __init__(self) -> None:
        self._memory: dict[UUID, dict[str, list[Any]]] = defaultdict(lambda: defaultdict(list))

    def append(self, project_id: UUID, category: str, value: Any) -> None:
        self._memory[project_id][category].append(value)

    def get(self, project_id: UUID, category: str) -> list[Any]:
        return list(self._memory[project_id].get(category, []))

    def context(self, project_id: UUID, categories: list[str]) -> dict[str, list[Any]]:
        return {category: self.get(project_id, category) for category in categories}
