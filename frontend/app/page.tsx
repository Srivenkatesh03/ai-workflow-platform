"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  Play, 
  Plus, 
  RefreshCw, 
  Trash2, 
  Edit2, 
  Database, 
  Cpu, 
  Wifi, 
  WifiOff, 
  X, 
  Loader2, 
  Code,
  AlertCircle,
  ArrowRight,
  Eye
} from "lucide-react";

import { Sidebar } from "@/components/sidebar";
import { StatusPill } from "@/components/status-pill";
import { useAuth } from "@/context/auth-context";
import { 
  fetchWorkflows, 
  fetchExecutions, 
  fetchQueueStatus, 
  createWorkflow, 
  deleteWorkflow, 
  executeWorkflow, 
  retryExecution,
  BackendWorkflowRead,
  ExecutionRead,
  QueueStatusRead,
  BackendWorkflowStep,
  StepExecutionRead,
  fetchAILogs,
  AILogRead
} from "@/services/workflow";
import { apiRequest } from "@/services/api";
import { ApiResponse } from "@/types/auth";
import { useWebsocket, WebSocketEvent } from "@/hooks/use-websocket";

export default function Home() {
  const { user } = useAuth();
  
  // View state and dynamic datasets
  const [activeView, setActiveView] = useState("dashboard");
  const [aiLogs, setAILogs] = useState<AILogRead[]>([]);
  
  // Data states
  const [workflows, setWorkflows] = useState<BackendWorkflowRead[]>([]);
  const [executions, setExecutions] = useState<ExecutionRead[]>([]);
  const [queueStatus, setQueueStatus] = useState<QueueStatusRead | null>(null);
  
  // Loading & Error states
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);
  
  // Modal states
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isRunOpen, setIsRunOpen] = useState(false);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  
  // Selected resource states
  const [selectedWorkflow, setSelectedWorkflow] = useState<BackendWorkflowRead | null>(null);
  const [selectedExecution, setSelectedExecution] = useState<ExecutionRead | null>(null);
  
  // Action submitting states
  const [isSubmittingAction, setIsSubmittingAction] = useState(false);
  
  // Form states
  const [workflowName, setWorkflowName] = useState("");
  const [workflowDesc, setWorkflowDesc] = useState("");
  const [workflowTrigger, setWorkflowTrigger] = useState("manual");
  const [workflowSteps, setWorkflowSteps] = useState<BackendWorkflowStep[]>([]);
  
  // Run payload state
  const [runPayload, setRunPayload] = useState("{\n  \"text\": \"Welcome to the AI Workflow Automation Platform!\"\n}");

  // Polling ref
  const pollingInterval = useRef<NodeJS.Timeout | null>(null);

  // Load all dashboard data
  async function loadData(silent = false) {
    if (!silent) setIsLoading(true);
    else setIsRefreshing(true);
    
    setError(null);
    try {
      const [wfs, execs, qStatus, logs] = await Promise.all([
        fetchWorkflows(),
        fetchExecutions(),
        fetchQueueStatus().catch(err => {
          console.warn("Queue status API failed:", err);
          return null; // fallback gracefully if queue/status fails
        }),
        fetchAILogs().catch(err => {
          console.warn("AI Logs API failed:", err);
          return [];
        })
      ]);
      
      setWorkflows(wfs);
      setExecutions(execs);
      if (qStatus) setQueueStatus(qStatus);
      setAILogs(logs);
    } catch (err: any) {
      console.error("Dashboard failed to fetch live data:", err);
      setError(err?.message ?? "Failed to connect to backend APIs. Make sure the backend server is running.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }

  // Handle incoming realtime events from WebSocket Connection
  const handleRealtimeEvent = useCallback((event: WebSocketEvent) => {
    const { event: eventName, execution_id, workflow_id, timestamp, data } = event;

    if (eventName === "queue_updated") {
      setQueueStatus(data as QueueStatusRead);
      return;
    }

    // Refresh workflows and AI logs list dynamically on creations/completions
    if (eventName === "workflow_completed" || eventName === "workflow_queued") {
      fetchWorkflows().then(setWorkflows).catch(console.error);
      fetchAILogs().then(setAILogs).catch(console.error);
    }

    // Helper state synchronizer for both main list and execution viewer
    const updateExecutionInState = (updater: (ex: ExecutionRead) => ExecutionRead) => {
      setExecutions(prev => {
        const index = prev.findIndex(ex => ex.id === execution_id);
        if (index === -1) {
          // If not found in the list yet, insert a new placeholder log
          if (eventName === "workflow_queued" || eventName === "workflow_started") {
            const newEx: ExecutionRead = {
              id: execution_id,
              workflow_id: workflow_id,
              status: (data.status as any) || "pending",
              started_at: timestamp,
              completed_at: null,
              step_executions: []
            };
            return [newEx, ...prev];
          }
          return prev;
        }
        return prev.map(ex => ex.id === execution_id ? updater(ex) : ex);
      });

      setSelectedExecution(prev => {
        if (!prev || prev.id !== execution_id) return prev;
        return updater(prev);
      });
    };

    // Realtime action dispatcher
    switch (eventName) {
      case "workflow_queued":
        showToast(`Workflow enqueued in Celery: ${data.workflow_name}`);
        updateExecutionInState(ex => ({
          ...ex,
          status: "pending",
          started_at: timestamp
        }));
        break;

      case "workflow_started":
        showToast(`Execution started: ${data.workflow_name}`);
        updateExecutionInState(ex => ({
          ...ex,
          status: "running",
          started_at: data.started_at || timestamp
        }));
        break;

      case "step_started":
        updateExecutionInState(ex => {
          const newStep: StepExecutionRead = {
            id: data.step_id,
            execution_id: execution_id,
            step_id: data.step_id,
            status: "running",
            failure_reason: null,
            retry_count: 0,
            duration_sec: 0,
            results: null,
            created_at: timestamp,
            updated_at: null,
            step_type: data.step_type,
            step_order: data.step_order
          };
          const exists = ex.step_executions.some(s => s.id === data.step_id);
          const updatedSteps = exists 
            ? ex.step_executions.map(s => s.id === data.step_id ? { ...s, status: "running" } : s)
            : [...ex.step_executions, newStep];
          
          return {
            ...ex,
            status: "running",
            step_executions: updatedSteps.sort((a, b) => (a.step_order ?? 0) - (b.step_order ?? 0))
          };
        });
        break;

      case "retry_triggered":
        updateExecutionInState(ex => {
          return {
            ...ex,
            status: "retrying",
            step_executions: ex.step_executions.map(s => 
              s.id === data.step_id 
                ? { ...s, status: "retrying", retry_count: data.retry_count, failure_reason: data.failure_reason } 
                : s
            )
          };
        });
        break;

      case "step_completed":
        updateExecutionInState(ex => {
          return {
            ...ex,
            step_executions: ex.step_executions.map(s => 
              s.id === data.step_id 
                ? { ...s, status: "completed", duration_sec: data.duration_sec, results: data.results } 
                : s
            )
          };
        });
        break;

      case "step_failed":
        updateExecutionInState(ex => {
          return {
            ...ex,
            step_executions: ex.step_executions.map(s => 
              s.id === data.step_id 
                ? { ...s, status: "failed", duration_sec: data.duration_sec, failure_reason: data.failure_reason } 
                : s
            )
          };
        });
        break;

      case "workflow_completed":
        if (data.status === "completed") {
          showToast(`Workflow execution succeeded: ${data.workflow_name}`);
        } else {
          showToast(`Workflow execution failed: ${data.message}`, "error");
        }
        updateExecutionInState(ex => ({
          ...ex,
          status: data.status,
          completed_at: data.completed_at || timestamp
        }));
        break;

      default:
        break;
    }
  }, [selectedExecution]);

  // Connect to live WebSocket events and state streams
  const { isConnected, isConnecting, queueMetrics } = useWebsocket(handleRealtimeEvent);

  // Sync real-time queue states directly from WebSockets
  useEffect(() => {
    if (queueMetrics) {
      setQueueStatus(queueMetrics);
    }
  }, [queueMetrics]);

  // Initial load and connection-aware polling backup
  useEffect(() => {
    loadData();

    // Poll live server metrics only if the WebSocket goes offline
    pollingInterval.current = setInterval(() => {
      if (!isConnected) {
        loadData(true);
      }
    }, 4000);

    return () => {
      if (pollingInterval.current) {
        clearInterval(pollingInterval.current);
      }
    };
  }, [isConnected]);

  // Show a toast message
  function showToast(message: string, type: "success" | "error" = "success") {
    setNotification({ message, type });
    setTimeout(() => {
      setNotification(null);
    }, 5000);
  }

  // Handle manual data refresh
  async function handleRefresh() {
    setIsRefreshing(true);
    await loadData(true);
    showToast("Dashboard data updated");
  }

  // Delete Workflow Action
  async function handleDeleteWorkflow(id: string, name: string) {
    if (!confirm(`Are you sure you want to delete the workflow "${name}"?`)) return;
    
    try {
      await deleteWorkflow(id);
      showToast(`Workflow "${name}" deleted successfully.`);
      loadData(true);
    } catch (err: any) {
      showToast(err?.message ?? "Failed to delete workflow", "error");
    }
  }

  // Open Edit Workflow Modal
  function handleOpenEdit(workflow: BackendWorkflowRead) {
    setSelectedWorkflow(workflow);
    setWorkflowName(workflow.name);
    setWorkflowDesc(workflow.description || "");
    setWorkflowTrigger(workflow.trigger_type);
    setIsEditOpen(true);
  }

  // Save/Update Workflow (Only name/description/status as per Backend Schemas)
  async function handleUpdateWorkflow(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedWorkflow) return;
    
    setIsSubmittingAction(true);
    try {
      await apiRequest<ApiResponse<any>>(`/workflows/${selectedWorkflow.id}`, {
        method: "PUT",
        body: {
          name: workflowName,
          description: workflowDesc,
          trigger_type: workflowTrigger
        }
      });
      showToast(`Workflow "${workflowName}" updated successfully.`);
      setIsEditOpen(false);
      loadData(true);
    } catch (err: any) {
      showToast(err?.message ?? "Failed to update workflow", "error");
    } finally {
      setIsSubmittingAction(false);
    }
  }

  // Create Workflow Action
  async function handleCreateWorkflow(e: React.FormEvent) {
    e.preventDefault();
    if (!workflowName.trim() || workflowName.trim().length < 2) {
      showToast("Workflow name must be at least 2 characters.", "error");
      return;
    }

    setIsSubmittingAction(true);
    try {
      await createWorkflow({
        name: workflowName,
        description: workflowDesc,
        trigger_type: workflowTrigger,
        steps: workflowSteps
      });
      
      showToast(`Workflow "${workflowName}" created successfully!`);
      setIsCreateOpen(false);
      resetCreateForm();
      loadData(true);
    } catch (err: any) {
      showToast(err?.message ?? "Failed to create workflow", "error");
    } finally {
      setIsSubmittingAction(false);
    }
  }

  function resetCreateForm() {
    setWorkflowName("");
    setWorkflowDesc("");
    setWorkflowTrigger("manual");
    setWorkflowSteps([]);
  }

  // Add Step to Creator Form
  function addStepToCreator(type: string) {
    let defaultConfig: Record<string, any> = {};
    if (type === "ai_summarize") {
      defaultConfig = { text: "Summarize: {{ payload.text }}", max_retries: 2, backoff_factor: 1.5 };
    } else if (type === "ai_classify") {
      defaultConfig = { labels: ["urgent", "normal", "low"], text: "{{ payload.text }}" };
    } else if (type === "notify") {
      defaultConfig = { channel: "slack", recipient: "ops-channel", message: "Workflow executed with ID: {{ execution_id }}" };
    } else if (type === "webhook_call") {
      defaultConfig = { url: "https://httpbin.org/post", method: "POST" };
    } else if (type === "approval") {
      defaultConfig = { approver: "admin@example.com" };
    }

    const nextOrder = workflowSteps.length + 1;
    setWorkflowSteps([
      ...workflowSteps,
      {
        step_order: nextOrder,
        step_type: type,
        configuration: defaultConfig
      }
    ]);
  }

  // Remove Step from Creator Form
  function removeStepFromCreator(index: number) {
    const updated = workflowSteps.filter((_, idx) => idx !== index);
    // re-order step_order sequentially
    const reordered = updated.map((step, idx) => ({
      ...step,
      step_order: idx + 1
    }));
    setWorkflowSteps(reordered);
  }

  // Open Run Execution Modal
  function handleOpenRun(workflow: BackendWorkflowRead) {
    setSelectedWorkflow(workflow);
    // Pre-populate payload suggestions based on name
    if (workflow.name.toLowerCase().includes("resume")) {
      setRunPayload(JSON.stringify({ text: "Candidate John has 5 years of Python experience, specialized in FastAPI, Docker, and Kubernetes.", email: "candidate@example.com" }, null, 2));
    } else if (workflow.name.toLowerCase().includes("invoice")) {
      setRunPayload(JSON.stringify({ amount: 4500, vendor: "Acme Corp", items: ["Server Hosting", "Domain Registration"] }, null, 2));
    } else {
      setRunPayload(JSON.stringify({ text: "Please summarize this task and alert the operators." }, null, 2));
    }
    setIsRunOpen(true);
  }

  // Run/Execute Workflow Action
  async function handleExecuteWorkflow(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedWorkflow) return;
    
    let parsedPayload = {};
    try {
      parsedPayload = JSON.parse(runPayload);
    } catch (err) {
      showToast("Invalid JSON payload format.", "error");
      return;
    }

    setIsSubmittingAction(true);
    try {
      const execution = await executeWorkflow(selectedWorkflow.id, parsedPayload);
      showToast(`Workflow execution enqueued. Execution ID: ${execution.id}`);
      setIsRunOpen(false);
      loadData(true);
    } catch (err: any) {
      showToast(err?.message ?? "Failed to queue workflow execution", "error");
    } finally {
      setIsSubmittingAction(false);
    }
  }

  // Retry Failed Execution Action
  async function handleRetry(executionId: string) {
    try {
      await retryExecution(executionId);
      showToast("Retry queued successfully!");
      loadData(true);
    } catch (err: any) {
      showToast(err?.message ?? "Failed to retry execution", "error");
    }
  }

  // Map backend workflows to compute executions & success rate dynamically from actual execution logs
  const mappedWorkflows = workflows.map(wf => {
    const wfExecs = executions.filter(ex => ex.workflow_id === wf.id);
    const executionsCount = wfExecs.length;
    const completedCount = wfExecs.filter(ex => ex.status === "completed").length;
    const successRate = executionsCount > 0 ? Math.round((completedCount / executionsCount) * 100) : 100;
    
    return {
      ...wf,
      executions: executionsCount,
      successRate
    };
  });

  // Calculate live stats
  const activeWorkflowsCount = workflows.length;
  const completedExecs = executions.filter(ex => ex.status === "completed");
  
  // Completed today filter (last 24 hours)
  const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;
  const completedTodayCount = completedExecs.filter(ex => {
    if (!ex.completed_at) return false;
    return new Date(ex.completed_at).getTime() > oneDayAgo;
  }).length;

  // Average runtime
  let totalRuntimeSec = 0;
  let hasRuntimeCount = 0;
  completedExecs.forEach(ex => {
    if (ex.started_at && ex.completed_at) {
      const start = new Date(ex.started_at).getTime();
      const end = new Date(ex.completed_at).getTime();
      const diff = (end - start) / 1000;
      if (diff > 0) {
        totalRuntimeSec += diff;
        hasRuntimeCount++;
      }
    }
  });
  const avgRuntime = hasRuntimeCount > 0 ? `${Math.round(totalRuntimeSec / hasRuntimeCount)}s` : "0s";
  
  const needsReviewCount = executions.filter(ex => ex.status === "failed").length;

  const stats = [
    { label: "Active workflows", value: activeWorkflowsCount.toString(), icon: Activity },
    { label: "Completed today", value: completedTodayCount.toString(), icon: CheckCircle2 },
    { label: "Avg. runtime", value: avgRuntime, icon: Clock },
    { label: "Needs review", value: needsReviewCount.toString(), icon: AlertTriangle }
  ];

  // Helper to resolve workflow name from ID
  function getWorkflowName(wfId: string) {
    const found = workflows.find(w => w.id === wfId);
    return found ? found.name : "Unknown Workflow";
  }

  // Get execution details and human message
  function getExecutionMessage(ex: ExecutionRead) {
    if (ex.status === "completed") {
      return "All steps finished successfully.";
    }
    if (ex.status === "failed") {
      const failedStep = ex.step_executions.find(s => s.status === "failed");
      if (failedStep) {
        const stepName = failedStep.step_type 
          ? failedStep.step_type.toUpperCase() 
          : `ID ${failedStep.step_id.substring(0, 8)}`;
        return `Failed at step ${stepName}: ${failedStep.failure_reason || "Unknown error"}`;
      }
      return "Execution failed, process halted.";
    }
    if (ex.status === "running") {
      const currentStep = ex.step_executions.find(s => s.status === "running");
      if (currentStep) {
        const stepName = currentStep.step_type 
          ? currentStep.step_type.toUpperCase() 
          : `ID ${currentStep.step_id.substring(0, 8)}`;
        const orderText = currentStep.step_order ? ` (order ${currentStep.step_order})` : "";
        return `Running step ${stepName}${orderText}...`;
      }
      return "Processing steps...";
    }
    if (ex.status === "retrying") {
      return "Step failure triggered dynamic backoff retry...";
    }
    return "Queued and waiting for active Celery workers.";
  }

  return (
    <main className="flex min-h-screen bg-panel text-ink relative">
      {/* Toast Alert Banner */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg border shadow-xl transition-all duration-300 transform scale-100 ${
          notification.type === "success" 
            ? "bg-emerald-50 border-emerald-200 text-emerald-800" 
            : "bg-red-50 border-red-200 text-red-800"
        }`}>
          {notification.type === "success" ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          <span className="text-sm font-medium">{notification.message}</span>
        </div>
      )}

      <Sidebar activeView={activeView} onViewChange={setActiveView} />
      
      <section className="min-w-0 flex-1 flex flex-col">
        {/* Header */}
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-line bg-white px-4 py-4 md:px-7">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl font-bold tracking-tight">
                {activeView === "dashboard" && "Workflow Operations"}
                {activeView === "workflows" && "Workflow Registry"}
                {activeView === "executions" && "Executions Ledger"}
                {activeView === "ai-logs" && "AI Latency & Analytics"}
                {activeView === "documents" && "File Storage"}
                {activeView === "alerts" && "Operations Alerts"}
              </h1>
              {isRefreshing && <Loader2 size={16} className="text-slate-400 animate-spin" />}
              
              {/* Pulsing Live Connection Status Pill */}
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold border transition-all duration-300 ${
                isConnected 
                  ? "bg-emerald-50 border-emerald-200 text-emerald-800" 
                  : isConnecting 
                  ? "bg-amber-50 border-amber-200 text-amber-800" 
                  : "bg-red-50 border-red-200 text-red-800"
              }`}>
                <span className={`h-1.5 w-1.5 rounded-full ${
                  isConnected ? "bg-emerald-500 animate-pulse" : isConnecting ? "bg-amber-500 animate-bounce" : "bg-red-500"
                }`} />
                {isConnected ? "Live Stream Connected" : isConnecting ? "Reconnecting stream..." : "Stream Offline"}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              {activeView === "dashboard" && "Monitor executions, queue statuses, and sequential AI tasks in realtime."}
              {activeView === "workflows" && "Manage and orchestrate sequential steps and AI prompts."}
              {activeView === "executions" && "Audit the detailed history of all automation runs."}
              {activeView === "ai-logs" && "Analyze LLM response speeds, token usage counts, and prompts."}
              {activeView === "documents" && "Access safe PDF resume indices and parsed contents."}
              {activeView === "alerts" && "Manage operations warnings and Slack routing rules."}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={handleRefresh}
              className="flex h-10 items-center gap-2 rounded-lg border border-line bg-white px-3 text-sm font-medium text-slate-700 hover:bg-slate-50 hover:text-black transition-colors"
              title="Refresh all data"
            >
              <RefreshCw size={15} className={`${isRefreshing ? "animate-spin" : ""}`} />
              Refresh
            </button>
            <button 
              onClick={() => { resetCreateForm(); setIsCreateOpen(true); }}
              className="flex h-10 items-center gap-2 rounded-lg bg-ink px-4 text-sm font-semibold text-white shadow-md hover:bg-black transition-transform active:scale-95"
            >
              <Plus size={16} aria-hidden="true" />
              New Workflow
            </button>
          </div>
        </header>

        {/* Error State Banner */}
        {error && (
          <div className="mx-4 mt-5 md:mx-7 p-4 border border-red-200 bg-red-50/50 rounded-lg flex items-start gap-3">
            <AlertCircle className="text-red-700 mt-0.5 flex-shrink-0" size={18} />
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-red-800">Connection Error</h3>
              <p className="mt-1 text-xs text-red-700">{error}</p>
              <button 
                onClick={() => loadData()}
                className="mt-3 flex h-8 items-center gap-1.5 rounded bg-red-700 px-3 text-xs font-semibold text-white hover:bg-red-800 transition-colors"
              >
                <RefreshCw size={12} />
                Try Reconnect
              </button>
            </div>
          </div>
        )}

        {/* Dashboard Content */}
        {activeView === "dashboard" && (
          <div className="flex-1 px-4 py-5 md:px-7 space-y-5 overflow-y-auto">
          {/* Stats Section */}
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map((stat) => {
              const Icon = stat.icon;
              return (
                <div key={stat.label} className="rounded-xl border border-line bg-white p-5 shadow-sm transition-all duration-300 hover:shadow-md">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{stat.label}</p>
                    <div className="h-8 w-8 rounded-lg bg-panel flex items-center justify-center text-slate-500 border border-slate-100">
                      <Icon size={16} aria-hidden="true" />
                    </div>
                  </div>
                  <p className="mt-3 text-3xl font-bold tracking-tight text-ink">{isLoading ? "---" : stat.value}</p>
                </div>
              );
            })}
          </section>

          {/* Queue Status Dashboard */}
          <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-line pb-4 mb-4">
              <div className="flex items-center gap-2">
                <Database size={18} className="text-slate-600" />
                <h2 className="text-sm font-bold tracking-tight">Queue Status Dashboard</h2>
              </div>
              {queueStatus && (
                <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${
                  queueStatus.redis_connected 
                    ? "bg-emerald-50 border-emerald-200 text-emerald-800" 
                    : "bg-red-50 border-red-200 text-red-800"
                }`}>
                  {queueStatus.redis_connected ? <Wifi size={13} /> : <WifiOff size={13} />}
                  {queueStatus.redis_connected ? "Broker Connected" : "Broker Offline"}
                </div>
              )}
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-lg bg-panel border border-line/60 p-4">
                <p className="text-xs text-slate-500">Active Workers</p>
                <div className="mt-2 flex items-center gap-2">
                  <Cpu size={16} className="text-teal-600 animate-pulse" />
                  <p className="text-xl font-bold">{queueStatus ? queueStatus.active_workers : 0}</p>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">Ready to pull tasks from Redis</p>
              </div>

              <div className="rounded-lg bg-panel border border-line/60 p-4">
                <p className="text-xs text-slate-500">Tasks In Queue</p>
                <div className="mt-2 flex items-center gap-2">
                  <Activity size={16} className="text-amber" />
                  <p className="text-xl font-bold">{queueStatus ? queueStatus.queue_length : 0}</p>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">Celery queue length of default queue</p>
              </div>

              <div className="rounded-lg bg-panel border border-line/60 p-4">
                <p className="text-xs text-slate-500">Broker Address</p>
                <div className="mt-2 flex items-center gap-2">
                  <Code size={16} className="text-slate-600" />
                  <p className="text-sm font-semibold truncate">redis://redis:6379/0</p>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">Standard backend message bus</p>
              </div>
            </div>
          </section>

          {/* Table & Logs layout */}
          <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_410px]">
            {/* Workflow Queue List */}
            <div className="rounded-xl border border-line bg-white shadow-sm flex flex-col">
              <div className="flex items-center justify-between border-b border-line px-5 py-4">
                <div>
                  <h2 className="text-sm font-bold tracking-tight">Workflow Engine</h2>
                  <p className="text-[11px] text-slate-400 mt-0.5">Manage and run sequential step configurations.</p>
                </div>
              </div>

              {isLoading ? (
                /* Skeleton Loader */
                <div className="p-5 space-y-4">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="h-16 w-full bg-panel animate-pulse rounded border border-line/50" />
                  ))}
                </div>
              ) : mappedWorkflows.length === 0 ? (
                /* Empty state */
                <div className="p-10 text-center flex flex-col items-center justify-center">
                  <div className="h-12 w-12 rounded-full bg-panel flex items-center justify-center text-slate-400 border border-line mb-3">
                    <Activity size={20} />
                  </div>
                  <h3 className="text-sm font-bold text-ink">No workflows configured</h3>
                  <p className="mt-1 text-xs text-slate-500 max-w-sm">Create your first sequential workflow to start processing AI tasks, notifications, and webhook requests.</p>
                  <button 
                    onClick={() => setIsCreateOpen(true)}
                    className="mt-4 flex h-9 items-center gap-2 rounded bg-ink px-4 text-xs font-semibold text-white shadow hover:bg-black transition-all"
                  >
                    <Plus size={14} />
                    Add First Workflow
                  </button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[680px] border-collapse text-sm text-left">
                    <thead className="bg-panel text-slate-500 text-[10px] font-bold uppercase tracking-wider border-b border-line">
                      <tr>
                        <th className="px-5 py-3.5">Workflow Details</th>
                        <th className="px-4 py-3.5">Trigger</th>
                        <th className="px-4 py-3.5">Status</th>
                        <th className="px-4 py-3.5 text-center">Executions</th>
                        <th className="px-4 py-3.5 text-center">Success Rate</th>
                        <th className="px-5 py-3.5 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line/60">
                      {mappedWorkflows.map((workflow) => (
                        <tr key={workflow.id} className="hover:bg-panel/40 transition-colors">
                          <td className="px-5 py-4">
                            <p className="font-semibold text-ink leading-snug">{workflow.name}</p>
                            <p className="mt-1 max-w-sm text-xs text-slate-400 line-clamp-2 leading-relaxed">{workflow.description || "No description provided."}</p>
                          </td>
                          <td className="px-4 py-4 text-xs text-slate-600 font-mono capitalize">{workflow.trigger_type}</td>
                          <td className="px-4 py-4">
                            <span className="inline-flex items-center rounded-full bg-slate-50 border border-line/80 px-2 py-0.5 text-[10px] font-medium capitalize text-slate-600">
                              {workflow.status}
                            </span>
                          </td>
                          <td className="px-4 py-4 text-center font-semibold text-slate-700">{workflow.executions}</td>
                          <td className="px-4 py-4 text-center font-bold text-teal-700">
                            {workflow.successRate}%
                          </td>
                          <td className="px-5 py-4 text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              <button 
                                onClick={() => handleOpenRun(workflow)}
                                className="flex h-8 items-center gap-1 rounded bg-teal-50 px-2.5 text-xs font-semibold text-teal-800 border border-teal-100 hover:bg-teal-100 hover:text-teal-900 transition-colors"
                                title="Run this workflow"
                              >
                                <Play size={12} fill="currentColor" />
                                Run
                              </button>
                              <button 
                                onClick={() => handleOpenEdit(workflow)}
                                className="h-8 w-8 flex items-center justify-center rounded border border-line text-slate-500 hover:bg-panel hover:text-ink transition-colors"
                                title="Edit properties"
                              >
                                <Edit2 size={12} />
                              </button>
                              <button 
                                onClick={() => handleDeleteWorkflow(workflow.id, workflow.name)}
                                className="h-8 w-8 flex items-center justify-center rounded border border-red-100 text-red-500 hover:bg-red-50 hover:text-red-700 transition-colors"
                                title="Delete workflow"
                              >
                                <Trash2 size={12} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Execution Logs */}
            <div className="rounded-xl border border-line bg-white shadow-sm flex flex-col h-[520px]">
              <div className="border-b border-line px-5 py-4 flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-bold tracking-tight">Execution History</h2>
                  <p className="text-[11px] text-slate-400 mt-0.5">Real-time status updates of active jobs.</p>
                </div>
              </div>

              {isLoading ? (
                <div className="p-4 space-y-3">
                  {[1, 2, 3, 4].map(i => (
                    <div key={i} className="h-14 w-full bg-panel animate-pulse rounded" />
                  ))}
                </div>
              ) : executions.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-6">
                  <Clock size={22} className="text-slate-300 mb-2" />
                  <p className="text-xs font-semibold text-slate-500">No execution logs yet</p>
                  <p className="text-[10px] text-slate-400 mt-0.5">Trigger a workflow to view process histories.</p>
                </div>
              ) : (
                <div className="flex-1 overflow-y-auto divide-y divide-line/60">
                  {executions.map((log) => {
                    const formattedTime = log.started_at 
                      ? new Date(log.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) 
                      : "Pending";
                    return (
                      <div key={log.id} className="p-4 hover:bg-panel/20 transition-all group">
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-xs font-bold truncate text-slate-800">{getWorkflowName(log.workflow_id)}</p>
                          <StatusPill status={log.status} />
                        </div>
                        <p className="mt-2 text-xs text-slate-500 leading-normal line-clamp-2 pr-2">
                          {getExecutionMessage(log)}
                        </p>
                        
                        <div className="mt-3 flex items-center justify-between">
                          <span className="text-[10px] text-slate-400 font-mono">{formattedTime}</span>
                          
                          <div className="flex items-center gap-1.5 opacity-80 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => { setSelectedExecution(log); setIsDetailsOpen(true); }}
                              className="flex h-6 items-center gap-0.5 rounded border border-line bg-white px-2 text-[10px] font-semibold text-slate-600 hover:bg-panel hover:text-ink transition-colors"
                            >
                              <Eye size={10} />
                              Details
                            </button>

                            {log.status === "failed" && (
                              <button
                                onClick={() => handleRetry(log.id)}
                                className="flex h-6 items-center gap-0.5 rounded bg-amber-50 border border-amber/20 px-2 text-[10px] font-bold text-amber hover:bg-amber-100 transition-colors"
                              >
                                <RefreshCw size={9} />
                                Retry
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </section>
          </div>
        )}

        {/* VIEW 2: WORKFLOWS REGISTRY LIST */}
        {activeView === "workflows" && (
          <div className="flex-1 px-4 py-5 md:px-7 space-y-5 overflow-y-auto">
            <div className="rounded-xl border border-line bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between border-b border-line pb-4 mb-6">
                <div>
                  <h2 className="text-md font-bold tracking-tight text-ink">Active Workflow Registry</h2>
                  <p className="text-xs text-slate-400 mt-1">Configure multi-step steps, prompt logic, and manual triggers.</p>
                </div>
                <button 
                  onClick={() => { resetCreateForm(); setIsCreateOpen(true); }}
                  className="flex h-9 items-center gap-2 rounded-lg bg-ink px-4 text-xs font-semibold text-white shadow hover:bg-black transition-all"
                >
                  <Plus size={14} />
                  Add Workflow
                </button>
              </div>

              {isLoading ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {[1, 2, 3, 4].map(i => <div key={i} className="h-32 bg-panel animate-pulse rounded-lg" />)}
                </div>
              ) : mappedWorkflows.length === 0 ? (
                <div className="text-center py-10">
                  <Activity size={24} className="text-slate-300 mx-auto mb-2" />
                  <p className="text-xs font-bold text-slate-500">No workflows in registry.</p>
                </div>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {mappedWorkflows.map(wf => (
                    <div key={wf.id} className="border border-line rounded-xl bg-panel/30 p-5 flex flex-col justify-between hover:border-slate-400 transition-all duration-200">
                      <div>
                        <div className="flex items-start justify-between gap-3">
                          <h3 className="font-bold text-sm text-ink leading-tight">{wf.name}</h3>
                          <span className="inline-flex rounded-full bg-white px-2 py-0.5 text-[9px] font-bold text-slate-600 border border-line leading-none">
                            {wf.trigger_type}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-2 line-clamp-3 leading-relaxed">{wf.description || "No description provided."}</p>
                      </div>

                      <div className="mt-6 border-t border-line/60 pt-4 flex items-center justify-between text-xs">
                        <div>
                          <p className="text-[10px] text-slate-400 uppercase">Runs</p>
                          <p className="font-bold text-slate-700 mt-0.5">{wf.executions}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-slate-400 uppercase">Success</p>
                          <p className="font-bold text-teal-700 mt-0.5">{wf.successRate}%</p>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <button 
                            onClick={() => handleOpenRun(wf)}
                            className="h-8 w-8 rounded-full border border-teal-100 bg-teal-50 flex items-center justify-center text-teal-800 hover:bg-teal-100"
                            title="Run"
                          >
                            <Play size={11} fill="currentColor" />
                          </button>
                          <button 
                            onClick={() => handleOpenEdit(wf)}
                            className="h-8 w-8 rounded-full border border-line bg-white flex items-center justify-center text-slate-500 hover:bg-panel"
                            title="Edit"
                          >
                            <Edit2 size={11} />
                          </button>
                          <button 
                            onClick={() => handleDeleteWorkflow(wf.id, wf.name)}
                            className="h-8 w-8 rounded-full border border-red-100 bg-red-50/55 flex items-center justify-center text-red-500 hover:bg-red-50"
                            title="Delete"
                          >
                            <Trash2 size={11} />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* VIEW 3: DEDICATED EXECUTIONS MONITOR */}
        {activeView === "executions" && (
          <div className="flex-1 px-4 py-5 md:px-7 space-y-5 overflow-y-auto">
            <div className="rounded-xl border border-line bg-white p-6 shadow-sm">
              <h2 className="text-md font-bold tracking-tight text-ink border-b border-line pb-4 mb-4">Executions Ledger</h2>
              
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map(i => <div key={i} className="h-12 w-full bg-panel animate-pulse rounded-lg" />)}
                </div>
              ) : executions.length === 0 ? (
                <div className="text-center py-10">
                  <Clock size={24} className="text-slate-300 mx-auto mb-2" />
                  <p className="text-xs font-bold text-slate-500">No execution logs found in ledger.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[700px] border-collapse text-sm text-left">
                    <thead className="bg-panel text-slate-500 text-[10px] font-bold uppercase border-b border-line">
                      <tr>
                        <th className="px-5 py-3">Execution ID</th>
                        <th className="px-4 py-3">Workflow</th>
                        <th className="px-4 py-3">Started</th>
                        <th className="px-4 py-3">Message Summary</th>
                        <th className="px-4 py-3 text-center">Status</th>
                        <th className="px-5 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line/60">
                      {executions.map(ex => {
                        const formattedTime = ex.started_at 
                          ? new Date(ex.started_at).toLocaleString() 
                          : "Pending";
                        return (
                          <tr key={ex.id} className="hover:bg-panel/30">
                            <td className="px-5 py-4 font-mono text-xs font-semibold text-slate-500">
                              {ex.id.substring(0, 8)}...
                            </td>
                            <td className="px-4 py-4 font-bold text-ink">{getWorkflowName(ex.workflow_id)}</td>
                            <td className="px-4 py-4 text-xs text-slate-500">{formattedTime}</td>
                            <td className="px-4 py-4 text-xs text-slate-600 max-w-xs truncate">{getExecutionMessage(ex)}</td>
                            <td className="px-4 py-4 text-center">
                              <StatusPill status={ex.status} />
                            </td>
                            <td className="px-5 py-4 text-right">
                              <div className="flex items-center justify-end gap-2">
                                <button
                                  onClick={() => { setSelectedExecution(ex); setIsDetailsOpen(true); }}
                                  className="flex h-8 items-center gap-1 rounded border border-line bg-white px-3 text-xs font-semibold text-slate-700 hover:bg-panel"
                                >
                                  <Eye size={12} />
                                  Timeline
                                </button>
                                {ex.status === "failed" && (
                                  <button
                                    onClick={() => handleRetry(ex.id)}
                                    className="flex h-8 items-center gap-1 rounded bg-amber-50 border border-amber/20 px-3 text-xs font-bold text-amber hover:bg-amber-100"
                                  >
                                    <RefreshCw size={11} />
                                    Retry
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* VIEW 4: AI LATENCY & ANALYTICS LEDGER */}
        {activeView === "ai-logs" && (
          <div className="flex-1 px-4 py-5 md:px-7 space-y-5 overflow-y-auto">
            <div className="rounded-xl border border-line bg-white p-6 shadow-sm">
              <h2 className="text-md font-bold tracking-tight text-ink border-b border-line pb-4 mb-6">AI Generation History</h2>
              
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map(i => <div key={i} className="h-14 w-full bg-panel animate-pulse rounded-lg" />)}
                </div>
              ) : aiLogs.length === 0 ? (
                <div className="text-center py-10">
                  <Database size={24} className="text-slate-300 mx-auto mb-2" />
                  <p className="text-xs font-bold text-slate-500 font-sans">No prompt generation logs found in database.</p>
                  <p className="text-[10px] text-slate-400 mt-1 max-w-sm mx-auto">Trigger a workflow containing AI Summarize or AI Classify steps to log LLM latency and token statistics.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[800px] border-collapse text-sm text-left">
                    <thead className="bg-panel text-slate-500 text-[10px] font-bold uppercase border-b border-line">
                      <tr>
                        <th className="px-5 py-3">Timestamp</th>
                        <th className="px-4 py-3">AI Model</th>
                        <th className="px-4 py-3">Provider</th>
                        <th className="px-4 py-3 text-center">Prompt Tokens</th>
                        <th className="px-4 py-3 text-center">Output Tokens</th>
                        <th className="px-4 py-3 text-center">Latency</th>
                        <th className="px-4 py-3 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line/60">
                      {aiLogs.map(log => {
                        const formattedTime = log.created_at 
                          ? new Date(log.created_at).toLocaleString() 
                          : "Pending";
                        return (
                          <tr key={log.id} className="hover:bg-panel/30">
                            <td className="px-5 py-4 text-xs text-slate-500 font-sans">{formattedTime}</td>
                            <td className="px-4 py-4 font-bold text-ink">
                              <span className="rounded bg-panel px-2 py-1 text-xs border border-line">
                                {log.model}
                              </span>
                            </td>
                            <td className="px-4 py-4 text-xs text-slate-600 font-mono capitalize">{log.provider}</td>
                            <td className="px-4 py-4 text-center font-mono text-slate-600">{log.prompt_tokens}</td>
                            <td className="px-4 py-4 text-center font-mono text-slate-600">{log.completion_tokens}</td>
                            <td className="px-4 py-4 text-center">
                              <span className="inline-flex items-center gap-1 font-semibold text-teal-800 font-mono text-xs bg-teal-50 border border-teal-100 rounded px-2 py-0.5">
                                <Clock size={11} />
                                {log.response_time_ms}ms
                              </span>
                            </td>
                            <td className="px-4 py-4 text-center">
                              <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-semibold border ${
                                log.success 
                                  ? "bg-emerald-50 border-emerald-200 text-emerald-800" 
                                  : "bg-red-50 border-red-200 text-red-800"
                              }`}>
                                {log.success ? "Success" : "Failed"}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* VIEW 5: DOCUMENTS PLACEHOLDER */}
        {activeView === "documents" && (
          <div className="flex-1 px-4 py-5 md:px-7 space-y-5 overflow-y-auto">
            <div className="rounded-xl border border-line bg-white p-8 text-center shadow-sm">
              <Eye size={32} className="text-slate-300 mx-auto mb-3" />
              <h3 className="text-md font-bold text-ink">Safe PDF Document Parser</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto mt-2 leading-relaxed">
                Phase 6 Document Processing pipelines are currently in progress. Soon, you will be able to securely upload resume PDF indexes, extract metadata, and pass them downstream directly into workflows.
              </p>
              <div className="mt-6 flex items-center justify-center gap-2">
                <span className="inline-flex items-center rounded bg-slate-50 border border-line px-2.5 py-0.5 text-xs text-slate-600 font-bold uppercase">
                  Upcoming release: Phase 6
                </span>
              </div>
            </div>
          </div>
        )}

        {/* VIEW 6: ALERTS PLACEHOLDER */}
        {activeView === "alerts" && (
          <div className="flex-1 px-4 py-5 md:px-7 space-y-5 overflow-y-auto">
            <div className="rounded-xl border border-line bg-white p-8 text-center shadow-sm">
              <AlertTriangle size={32} className="text-slate-300 mx-auto mb-3" />
              <h3 className="text-md font-bold text-ink">Operations Slack Alert Routing</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto mt-2 leading-relaxed">
                Phase 7 Notification Integrations are currently in development. You will soon configure dynamic SMTP servers and Slack Webhook endpoints to route failure alarms to your DevOps teams.
              </p>
              <div className="mt-6 flex items-center justify-center gap-2">
                <span className="inline-flex items-center rounded bg-slate-50 border border-line px-2.5 py-0.5 text-xs text-slate-600 font-bold uppercase">
                  Upcoming release: Phase 7
                </span>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* CREATE WORKFLOW MODAL */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-2xl rounded-xl border border-line bg-white shadow-2xl flex flex-col max-h-[90vh]">
            <div className="flex items-center justify-between border-b border-line px-6 py-4">
              <div>
                <h3 className="text-md font-bold text-ink">Create New Workflow</h3>
                <p className="text-[11px] text-slate-400 mt-0.5">Define metadata and sequential step parameters.</p>
              </div>
              <button 
                onClick={() => setIsCreateOpen(false)}
                className="h-8 w-8 rounded-full flex items-center justify-center hover:bg-panel border border-line/50 transition-colors text-slate-400 hover:text-ink"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleCreateWorkflow} className="flex-1 overflow-y-auto p-6 space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">Workflow Name</span>
                  <input
                    className="w-full h-10 border border-line rounded-lg px-3 outline-none focus:border-ink transition-colors text-sm"
                    value={workflowName}
                    onChange={(e) => setWorkflowName(e.target.value)}
                    placeholder="e.g. Resume Processing"
                    minLength={2}
                    maxLength={160}
                    required
                  />
                </label>

                <label className="block">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">Trigger Type</span>
                  <select
                    className="w-full h-10 border border-line bg-white rounded-lg px-3 outline-none focus:border-ink transition-colors text-sm"
                    value={workflowTrigger}
                    onChange={(e) => setWorkflowTrigger(e.target.value)}
                  >
                    <option value="manual">Manual Trigger</option>
                    <option value="webhook">Webhook Endpoint</option>
                  </select>
                </label>
              </div>

              <label className="block">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">Description</span>
                <textarea
                  className="w-full border border-line rounded-lg px-3 py-2 outline-none focus:border-ink transition-colors text-sm min-h-[60px]"
                  value={workflowDesc}
                  onChange={(e) => setWorkflowDesc(e.target.value)}
                  placeholder="Explain the operational role of this workflow..."
                />
              </label>

              {/* Step Builder */}
              <div className="border-t border-line pt-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">Sequential Steps ({workflowSteps.length})</span>
                  
                  {/* Step Selector Dropdown Buttons */}
                  <div className="flex flex-wrap gap-1">
                    <button
                      type="button"
                      onClick={() => addStepToCreator("ai_summarize")}
                      className="flex h-7 items-center gap-1 rounded bg-teal-50 border border-teal-100 px-2 text-[10px] font-bold text-teal-800 hover:bg-teal-100 transition-colors"
                    >
                      + AI Summarize
                    </button>
                    <button
                      type="button"
                      onClick={() => addStepToCreator("ai_classify")}
                      className="flex h-7 items-center gap-1 rounded bg-teal-50 border border-teal-100 px-2 text-[10px] font-bold text-teal-800 hover:bg-teal-100 transition-colors"
                    >
                      + AI Classify
                    </button>
                    <button
                      type="button"
                      onClick={() => addStepToCreator("notify")}
                      className="flex h-7 items-center gap-1 rounded bg-teal-50 border border-teal-100 px-2 text-[10px] font-bold text-teal-800 hover:bg-teal-100 transition-colors"
                    >
                      + Notify
                    </button>
                    <button
                      type="button"
                      onClick={() => addStepToCreator("webhook_call")}
                      className="flex h-7 items-center gap-1 rounded bg-teal-50 border border-teal-100 px-2 text-[10px] font-bold text-teal-800 hover:bg-teal-100 transition-colors"
                    >
                      + Webhook
                    </button>
                    <button
                      type="button"
                      onClick={() => addStepToCreator("approval")}
                      className="flex h-7 items-center gap-1 rounded bg-teal-50 border border-teal-100 px-2 text-[10px] font-bold text-teal-800 hover:bg-teal-100 transition-colors"
                    >
                      + Approval
                    </button>
                  </div>
                </div>

                {workflowSteps.length === 0 ? (
                  <div className="border border-dashed border-line rounded-lg p-5 text-center text-xs text-slate-400">
                    No steps added. Click the helper pills above to construct your sequence.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {workflowSteps.map((step, index) => (
                      <div key={index} className="flex items-center gap-3 p-3 bg-panel border border-line rounded-lg text-xs hover:border-slate-300 transition-colors">
                        <span className="h-5 w-5 rounded bg-ink text-white font-bold flex items-center justify-center">{step.step_order}</span>
                        <div className="flex-1">
                          <p className="font-bold text-ink uppercase tracking-tight">{step.step_type.replace("_", " ")}</p>
                          <p className="text-[10px] text-slate-400 mt-0.5 truncate max-w-sm">Config: {JSON.stringify(step.configuration)}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeStepFromCreator(index)}
                          className="h-6 w-6 rounded border border-red-100 bg-red-50/50 flex items-center justify-center text-red-500 hover:bg-red-50 transition-colors"
                        >
                          <X size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Action buttons */}
              <div className="border-t border-line pt-4 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="flex h-10 items-center justify-center rounded-lg border border-line px-4 text-xs font-semibold text-slate-600 hover:bg-panel hover:text-ink transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingAction || workflowSteps.length === 0}
                  className="flex h-10 items-center justify-center gap-1.5 rounded-lg bg-ink px-5 text-xs font-semibold text-white hover:bg-black transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmittingAction && <Loader2 size={13} className="animate-spin" />}
                  Create Workflow
                  <ArrowRight size={13} />
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EDIT PROPERTIES MODAL */}
      {isEditOpen && selectedWorkflow && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl border border-line bg-white shadow-2xl flex flex-col">
            <div className="flex items-center justify-between border-b border-line px-6 py-4">
              <div>
                <h3 className="text-md font-bold text-ink">Edit Properties</h3>
                <p className="text-[11px] text-slate-400 mt-0.5">Modify workflow names or description logs.</p>
              </div>
              <button 
                onClick={() => setIsEditOpen(false)}
                className="h-8 w-8 rounded-full flex items-center justify-center hover:bg-panel border border-line/50 transition-colors text-slate-400 hover:text-ink"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleUpdateWorkflow} className="p-6 space-y-4">
              <label className="block">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">Workflow Name</span>
                <input
                  className="w-full h-10 border border-line rounded-lg px-3 outline-none focus:border-ink transition-colors text-sm"
                  value={workflowName}
                  onChange={(e) => setWorkflowName(e.target.value)}
                  required
                />
              </label>

              <label className="block">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">Description</span>
                <textarea
                  className="w-full border border-line rounded-lg px-3 py-2 outline-none focus:border-ink transition-colors text-sm min-h-[80px]"
                  value={workflowDesc}
                  onChange={(e) => setWorkflowDesc(e.target.value)}
                />
              </label>

              <div className="border-t border-line pt-4 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsEditOpen(false)}
                  className="flex h-10 items-center justify-center rounded-lg border border-line px-4 text-xs font-semibold text-slate-600 hover:bg-panel hover:text-ink transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingAction}
                  className="flex h-10 items-center justify-center gap-1.5 rounded-lg bg-ink px-5 text-xs font-semibold text-white hover:bg-black transition-colors"
                >
                  {isSubmittingAction && <Loader2 size={13} className="animate-spin" />}
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* RUN WORKFLOW MODAL */}
      {isRunOpen && selectedWorkflow && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-line bg-white shadow-2xl flex flex-col">
            <div className="flex items-center justify-between border-b border-line px-6 py-4">
              <div>
                <h3 className="text-md font-bold text-ink">Execute: {selectedWorkflow.name}</h3>
                <p className="text-[11px] text-slate-400 mt-0.5">Input custom payload parameters to pass downstream.</p>
              </div>
              <button 
                onClick={() => setIsRunOpen(false)}
                className="h-8 w-8 rounded-full flex items-center justify-center hover:bg-panel border border-line/50 transition-colors text-slate-400 hover:text-ink"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleExecuteWorkflow} className="p-6 space-y-4">
              <label className="block">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">JSON Payload</span>
                <textarea
                  className="w-full border border-line rounded-lg px-3 py-2 outline-none focus:border-ink transition-colors text-xs min-h-[140px] font-mono leading-relaxed bg-panel"
                  value={runPayload}
                  onChange={(e) => setRunPayload(e.target.value)}
                  required
                />
              </label>

              <div className="border-t border-line pt-4 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsRunOpen(false)}
                  className="flex h-10 items-center justify-center rounded-lg border border-line px-4 text-xs font-semibold text-slate-600 hover:bg-panel hover:text-ink transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingAction}
                  className="flex h-10 items-center justify-center gap-1.5 rounded-lg bg-teal-800 px-5 text-xs font-semibold text-white hover:bg-teal-900 transition-colors shadow-md shadow-teal-800/10"
                >
                  {isSubmittingAction && <Loader2 size={13} className="animate-spin" />}
                  Execute Queue
                  <Play size={10} fill="currentColor" />
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EXECUTION DETAILS MODAL */}
      {isDetailsOpen && selectedExecution && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-3xl rounded-xl border border-line bg-white shadow-2xl flex flex-col max-h-[85vh]">
            <div className="flex items-center justify-between border-b border-line px-6 py-4 bg-panel/30">
              <div>
                <h3 className="text-md font-bold text-ink">Execution Summary</h3>
                <p className="text-[10px] text-slate-400 mt-1 font-mono uppercase">ID: {selectedExecution.id}</p>
              </div>
              <button 
                onClick={() => setIsDetailsOpen(false)}
                className="h-8 w-8 rounded-full flex items-center justify-center hover:bg-panel border border-line/50 transition-colors text-slate-400 hover:text-ink"
              >
                <X size={16} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Overall status bar */}
              <div className="grid gap-3 sm:grid-cols-3 p-4 bg-panel/50 border border-line/80 rounded-xl text-xs">
                <div>
                  <p className="text-slate-400">Triggered Workflow</p>
                  <p className="font-semibold text-ink mt-1 truncate">{getWorkflowName(selectedExecution.workflow_id)}</p>
                </div>
                <div>
                  <p className="text-slate-400">Status Summary</p>
                  <div className="mt-1">
                    <StatusPill status={selectedExecution.status} />
                  </div>
                </div>
                <div>
                  <p className="text-slate-400">Timing</p>
                  <p className="font-semibold text-slate-700 mt-1">
                    {selectedExecution.started_at 
                      ? new Date(selectedExecution.started_at).toLocaleTimeString() 
                      : "Pending"}
                  </p>
                </div>
              </div>

              {/* Steps timeline */}
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-4">Execution Sequence Timeline</span>
                
                {selectedExecution.step_executions.length === 0 ? (
                  <div className="border border-dashed border-line rounded-lg p-5 text-center text-xs text-slate-400">
                    No steps have started executing. The job is queued in the background Celery agent.
                  </div>
                ) : (
                  <div className="space-y-4 relative before:absolute before:left-5 before:top-2 before:bottom-2 before:w-0.5 before:bg-line/60">
                    {selectedExecution.step_executions.map((step, idx) => (
                      <div key={step.id} className="relative pl-10 flex flex-col sm:flex-row sm:items-start gap-4">
                        {/* Bullet count */}
                        <div className={`absolute left-2.5 top-0.5 h-6.5 w-6.5 rounded-full flex items-center justify-center text-[10px] font-bold border transition-colors ${
                          step.status === "completed" 
                            ? "bg-emerald-50 border-emerald-300 text-emerald-800" 
                            : step.status === "failed" 
                            ? "bg-red-50 border-red-300 text-red-800" 
                            : step.status === "running"
                            ? "bg-teal-50 border-teal-300 text-teal-800 animate-pulse"
                            : "bg-white border-line text-slate-400"
                        }`}>
                          {idx + 1}
                        </div>

                        {/* Step details block */}
                        <div className="flex-1 bg-panel border border-line/60 rounded-lg p-4 text-xs">
                          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line/40 pb-2 mb-2">
                            <div>
                              <p className="font-bold text-ink uppercase tracking-tight">
                                {step.step_type ? step.step_type.replace("_", " ") : `Step ${step.step_order ?? (idx + 1)}`}
                              </p>
                              <p className="text-[9px] text-slate-400 mt-0.5 font-mono">ID: {step.step_id}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              {step.duration_sec !== null && (
                                <span className="inline-flex items-center gap-0.5 font-semibold text-slate-500 font-mono text-[10px]">
                                  <Clock size={11} />
                                  {step.duration_sec.toFixed(2)}s
                                </span>
                              )}
                              <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[9px] font-semibold border ${
                                step.status === "completed" 
                                  ? "bg-emerald-50 border-emerald-100 text-emerald-800" 
                                  : step.status === "failed" 
                                  ? "bg-red-50 border-red-100 text-red-800" 
                                  : "bg-white border-line text-slate-600"
                              }`}>
                                {step.status}
                              </span>
                            </div>
                          </div>

                          {/* Failure info */}
                          {step.status === "failed" && step.failure_reason && (
                            <div className="p-2 border border-red-200 bg-red-50 rounded text-red-800 mb-3 font-medium">
                              Failure Reason: {step.failure_reason}
                            </div>
                          )}

                          {/* Retries */}
                          {step.retry_count > 0 && (
                            <p className="text-[10px] text-amber mb-3 font-semibold">
                              Retried {step.retry_count} times during backoff factors.
                            </p>
                          )}

                          {/* Raw Output Payload */}
                          {step.results && Object.keys(step.results).length > 0 && (
                            <div className="mt-2 space-y-1">
                              <span className="text-[9px] font-bold text-slate-400 block uppercase">Step Output Payload:</span>
                              <pre className="p-3 bg-white border border-line rounded-lg text-[10px] font-mono leading-relaxed overflow-x-auto text-slate-700 max-h-[140px]">
                                {JSON.stringify(step.results, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="border-t border-line px-6 py-4 flex items-center justify-end">
              <button
                onClick={() => setIsDetailsOpen(false)}
                className="flex h-10 items-center justify-center rounded-lg bg-ink px-5 text-xs font-semibold text-white hover:bg-black transition-colors"
              >
                Close Summary
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
