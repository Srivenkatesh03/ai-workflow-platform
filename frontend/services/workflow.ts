import { apiRequest } from "./api";
import type { ApiResponse } from "@/types/auth";
import type { WorkflowStatus } from "@/types/workflow";

export type BackendWorkflowStep = {
  step_order: number;
  step_type: string;
  configuration: Record<string, any>;
};

export type BackendWorkflowCreate = {
  name: string;
  description?: string;
  trigger_type: string;
  steps?: BackendWorkflowStep[];
};

export type BackendWorkflowRead = {
  id: string;
  name: string;
  description: string | null;
  trigger_type: string;
  status: string;
};

export type StepExecutionRead = {
  id: string;
  execution_id: string;
  step_id: string;
  status: string;
  failure_reason: string | null;
  retry_count: number;
  duration_sec: number | null;
  results: Record<string, any> | null;
  created_at: string;
  updated_at: string | null;
  step_type?: string;
  step_order?: number;
};

export type ExecutionRead = {
  id: string;
  workflow_id: string;
  status: WorkflowStatus;
  started_at: string | null;
  completed_at: string | null;
  step_executions: StepExecutionRead[];
};

export type QueueStatusRead = {
  redis_connected: boolean;
  queue_name: string;
  queue_length: number;
  active_workers: number;
  error: string | null;
};

export async function fetchWorkflows(): Promise<BackendWorkflowRead[]> {
  const response = await apiRequest<ApiResponse<BackendWorkflowRead[]>>("/workflows");
  return response.data;
}

export async function createWorkflow(workflow: BackendWorkflowCreate): Promise<BackendWorkflowRead> {
  const response = await apiRequest<ApiResponse<BackendWorkflowRead>>("/workflows", {
    method: "POST",
    body: workflow,
  });
  return response.data;
}

export async function deleteWorkflow(id: string): Promise<{ id: string }> {
  const response = await apiRequest<ApiResponse<{ id: string }>>(`/workflows/${id}`, {
    method: "DELETE",
  });
  return response.data;
}

export async function executeWorkflow(id: string, payload: Record<string, any> = {}): Promise<ExecutionRead> {
  const response = await apiRequest<ApiResponse<ExecutionRead>>(`/workflows/${id}/execute`, {
    method: "POST",
    body: { payload },
  });
  return response.data;
}

export async function fetchExecutions(): Promise<ExecutionRead[]> {
  const response = await apiRequest<ApiResponse<ExecutionRead[]>>("/executions");
  return response.data;
}

export async function retryExecution(executionId: string): Promise<ExecutionRead> {
  const response = await apiRequest<ApiResponse<ExecutionRead>>(`/executions/${executionId}/retry`, {
    method: "POST",
  });
  return response.data;
}

export async function fetchQueueStatus(): Promise<QueueStatusRead> {
  const response = await apiRequest<ApiResponse<QueueStatusRead>>("/queue/status");
  return response.data;
}

export type AILogRead = {
  id: string;
  provider: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  response_time_ms: number;
  workflow_id: string | null;
  execution_id: string | null;
  success: boolean;
  error_message: string | null;
  created_at: string;
};

export async function fetchAILogs(): Promise<AILogRead[]> {
  const response = await apiRequest<ApiResponse<AILogRead[]>>("/ai/logs");
  return response.data;
}

