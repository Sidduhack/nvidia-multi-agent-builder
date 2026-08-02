import json

from app.agents.definitions import AgentDefinition
from app.agents.protocol import AgentOutput
from app.models.router import ModelRouter
from app.providers.base import AIProvider, ChatMessage, CompletionRequest
from app.schemas.task import AgentTask


class AgentExecutionError(RuntimeError):
    pass


class AgentExecutor:
    def __init__(self, provider: AIProvider, router: ModelRouter) -> None:
        self.provider = provider
        self.router = router

    async def execute(
        self,
        definition: AgentDefinition,
        task: AgentTask,
        project_context: dict,
    ) -> AgentOutput:
        model = self.router.select(
            definition.required_capabilities,
            preferred_model=definition.preferred_model,
        )
        contract = {
            "summary": "string",
            "decisions": ["string"],
            "artifacts": {},
            "issues": [
                {
                    "type": "string",
                    "description": "string",
                    "affected_files": ["string"],
                    "proposed_solution": "string or null",
                    "requires_architect_review": False,
                }
            ],
            "suggested_tasks": [],
        }
        user_payload = {
            "task": task.model_dump(mode="json"),
            "project_context": project_context,
            "output_contract": contract,
        }
        response = await self.provider.complete(
            CompletionRequest(
                model=model.model_id,
                messages=[
                    ChatMessage(role="system", content=definition.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            "Return only one valid JSON object matching output_contract.\n"
                            + json.dumps(user_payload, default=str)
                        ),
                    ),
                ],
                temperature=0.1,
            )
        )
        try:
            return AgentOutput.model_validate_json(response.content)
        except (ValueError, json.JSONDecodeError) as exc:
            raise AgentExecutionError("Agent returned invalid structured output") from exc
