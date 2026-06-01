import { Activity, AlertTriangle, CheckCircle2, Clock, Play, Plus, RefreshCw, Search } from "lucide-react";

import { Sidebar } from "@/components/sidebar";
import { StatusPill } from "@/components/status-pill";
import { executionLogs, workflows } from "@/lib/sample-data";

const stats = [
  { label: "Active workflows", value: "18", icon: Activity },
  { label: "Completed today", value: "247", icon: CheckCircle2 },
  { label: "Avg. runtime", value: "42s", icon: Clock },
  { label: "Needs review", value: "6", icon: AlertTriangle }
];

export default function Home() {
  return (
    <main className="flex min-h-screen bg-panel text-ink">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-line bg-white px-4 py-4 md:px-7">
          <div>
            <h1 className="text-xl font-semibold">Workflow Operations</h1>
            <p className="mt-1 text-sm text-slate-500">Monitor executions, AI tasks, and automation health.</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="hidden h-10 items-center gap-2 rounded border border-line bg-white px-3 md:flex">
              <Search size={16} className="text-slate-400" aria-hidden="true" />
              <input className="w-56 outline-none" placeholder="Search workflows" aria-label="Search workflows" />
            </div>
            <button className="flex h-10 items-center gap-2 rounded bg-ink px-3 text-sm font-medium text-white">
              <Plus size={16} aria-hidden="true" />
              New Workflow
            </button>
          </div>
        </header>

        <div className="px-4 py-5 md:px-7">
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map((stat) => {
              const Icon = stat.icon;
              return (
                <div key={stat.label} className="rounded border border-line bg-white p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-slate-500">{stat.label}</p>
                    <Icon size={17} className="text-slate-500" aria-hidden="true" />
                  </div>
                  <p className="mt-3 text-2xl font-semibold">{stat.value}</p>
                </div>
              );
            })}
          </section>

          <section className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_390px]">
            <div className="rounded border border-line bg-white">
              <div className="flex items-center justify-between border-b border-line px-4 py-3">
                <h2 className="text-sm font-semibold">Workflow Queue</h2>
                <button className="flex h-9 items-center gap-2 rounded border border-line px-3 text-sm" title="Refresh workflow list">
                  <RefreshCw size={15} aria-hidden="true" />
                  Refresh
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px] border-collapse text-sm">
                  <thead className="bg-panel text-left text-xs uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Workflow</th>
                      <th className="px-4 py-3 font-semibold">Trigger</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                      <th className="px-4 py-3 font-semibold">Executions</th>
                      <th className="px-4 py-3 font-semibold">Success</th>
                      <th className="px-4 py-3 font-semibold">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {workflows.map((workflow) => (
                      <tr key={workflow.id} className="border-t border-line">
                        <td className="px-4 py-4">
                          <p className="font-medium">{workflow.name}</p>
                          <p className="mt-1 max-w-xl text-xs text-slate-500">{workflow.description}</p>
                        </td>
                        <td className="px-4 py-4 text-slate-600">{workflow.triggerType}</td>
                        <td className="px-4 py-4">
                          <StatusPill status={workflow.status} />
                        </td>
                        <td className="px-4 py-4">{workflow.executions}</td>
                        <td className="px-4 py-4">{workflow.successRate}%</td>
                        <td className="px-4 py-4">
                          <button className="flex h-9 items-center gap-2 rounded border border-line px-3 text-sm" title="Run workflow">
                            <Play size={15} aria-hidden="true" />
                            Run
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="rounded border border-line bg-white">
              <div className="border-b border-line px-4 py-3">
                <h2 className="text-sm font-semibold">Execution Logs</h2>
              </div>
              <div className="divide-y divide-line">
                {executionLogs.map((log) => (
                  <div key={log.id} className="px-4 py-4">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-medium">{log.workflow}</p>
                      <StatusPill status={log.status} />
                    </div>
                    <p className="mt-2 text-sm text-slate-600">{log.message}</p>
                    <p className="mt-2 text-xs text-slate-500">{log.timestamp}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}

