import type { ExecutionLog, Workflow } from "@/types/workflow";

export const workflows: Workflow[] = [
  {
    id: "wf_resume",
    name: "Resume Screening",
    description: "Parse candidate resumes, classify skills, and notify HR.",
    triggerType: "upload",
    status: "running",
    executions: 128,
    successRate: 96
  },
  {
    id: "wf_invoice",
    name: "Invoice Approval",
    description: "Extract invoice fields and route high-value invoices for review.",
    triggerType: "webhook",
    status: "completed",
    executions: 342,
    successRate: 93
  },
  {
    id: "wf_email",
    name: "Email Summarizer",
    description: "Summarize inbound operations emails and create action items.",
    triggerType: "scheduled",
    status: "pending",
    executions: 74,
    successRate: 91
  }
];

export const executionLogs: ExecutionLog[] = [
  {
    id: "log_001",
    workflow: "Resume Screening",
    status: "running",
    timestamp: "11:41 AM",
    message: "AI classification step started"
  },
  {
    id: "log_002",
    workflow: "Invoice Approval",
    status: "completed",
    timestamp: "11:37 AM",
    message: "Approval notification queued"
  },
  {
    id: "log_003",
    workflow: "Email Summarizer",
    status: "retrying",
    timestamp: "11:28 AM",
    message: "Provider timeout, retry scheduled"
  }
];

