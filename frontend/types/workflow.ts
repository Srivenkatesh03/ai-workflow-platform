export type WorkflowStatus = "pending" | "running" | "completed" | "failed" | "retrying";

export type Workflow = {
  id: string;
  name: string;
  description: string;
  triggerType: string;
  status: WorkflowStatus;
  executions: number;
  successRate: number;
};

export type ExecutionLog = {
  id: string;
  workflow: string;
  status: WorkflowStatus;
  timestamp: string;
  message: string;
};

