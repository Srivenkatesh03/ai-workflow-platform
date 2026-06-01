import type { WorkflowStatus } from "@/types/workflow";

const statusStyles: Record<WorkflowStatus, string> = {
  pending: "border-line bg-white text-ink",
  running: "border-teal-200 bg-teal-50 text-teal-800",
  completed: "border-emerald-200 bg-emerald-50 text-emerald-800",
  failed: "border-red-200 bg-red-50 text-red-800",
  retrying: "border-amber-200 bg-amber-50 text-amber-800"
};

export function StatusPill({ status }: { status: WorkflowStatus }) {
  return (
    <span className={`inline-flex h-7 items-center rounded border px-2 text-xs font-medium ${statusStyles[status]}`}>
      {status}
    </span>
  );
}

