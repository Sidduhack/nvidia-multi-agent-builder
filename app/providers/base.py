from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class CompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int | None = Field(default=None, gt=0)


class CompletionResponse(BaseModel):
    model: str
    content: str
    usage: dict[str, Any] = Field(default_factory=dict)


class AIProvider(ABC):
    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        raise NotImplementedError

    @abstractmethod
    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        raise NotImplementedError

    @abstractmethod
    async def list_models(self) -> list[str]:
        raise NotImplementedError
