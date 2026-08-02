from typing import Any

from pydantic import BaseModel, Field


class AgentIssue(BaseModel):
    type: str
    description: str
    affected_files: list[str] = Field(default_factory=list)
    proposed_solution: str | None = None
    requires_architect_review: bool = False


class AgentOutput(BaseModel):
    summary: str
    decisions: list[str] = Field(default_factory=list)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    issues: list[AgentIssue] = Field(default_factory=list)
    suggested_tasks: list[dict[str, Any]] = Field(default_factory=list)
