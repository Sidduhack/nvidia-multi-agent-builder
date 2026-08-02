import asyncio

from app.agents.definitions import AgentRegistry
from app.agents.executor import AgentExecutor
from app.events.bus import EventBus, ProjectEvent
from app.memory.project import ProjectMemory
from app.orchestrator.graph import TaskGraph
from app.schemas.task import AgentTask, TaskStatus


class Scheduler:
    def __init__(
        self,
        graph: TaskGraph,
        agents: AgentRegistry,
        executor: AgentExecutor,
        memory: ProjectMemory,
        events: EventBus,
        max_parallel: int = 2,
    ) -> None:
        self.graph = graph
        self.agents = agents
        self.executor = executor
        self.memory = memory
        self.events = events
        self.semaphore = asyncio.Semaphore(max_parallel)

    async def run_ready(self) -> list[AgentTask]:
        ready = self.graph.ready()
        await asyncio.gather(*(self._run(task) for task in ready))
        return ready

    async def _run(self, task: AgentTask) -> None:
        async with self.semaphore:
            task.status = TaskStatus.RUNNING
            await self.events.publish(
                ProjectEvent(project_id=task.project_id, type="AGENT_STARTED", payload={"task_id": str(task.id), "agent": task.agent})
            )
            try:
                definition = self.agents.get(task.agent)
                context = self.memory.context(
                    task.project_id,
                    ["requirements", "architecture", "api_contracts", "database_schema", "decisions"],
                )
                result = await self.executor.execute(definition, task, context)
                self.memory.append(task.project_id, f"agent:{task.agent}", result.model_dump())
                self.memory.append(task.project_id, "decisions", result.decisions)
                task.status = TaskStatus.COMPLETED
                await self.events.publish(
                    ProjectEvent(project_id=task.project_id, type="TASK_COMPLETED", payload={"task_id": str(task.id), "agent": task.agent, "summary": result.summary})
                )
            except Exception as exc:
                task.status = TaskStatus.FAILED
                await self.events.publish(
                    ProjectEvent(project_id=task.project_id, type="TASK_FAILED", payload={"task_id": str(task.id), "agent": task.agent, "error_type": type(exc).__name__})
                )
