export type TaskStatus = "pending" | "planning" | "running" | "waiting" | "reviewing" | "testing" | "failed" | "repairing" | "completed" | "escalated" | "cancelled";

export interface ProjectCreateRequest { name: string; prompt: string; }
export interface ProjectResponse { id: string; name: string; prompt: string; status: string; current_version: number; }
export interface TaskResponse { id: string; project_id: string; agent: string; objective: string; dependencies: string[]; status: TaskStatus; review_required: boolean; }
export interface AgentStatusResponse { name: string; description: string; enabled: boolean; current_task_id: string | null; status: string; }
export interface ApiError { code: string; message: string; details: Record<string, unknown>; }
