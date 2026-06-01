import { Activity, Bell, Bot, FileText, LayoutDashboard, Workflow } from "lucide-react";

const items = [
  { label: "Dashboard", icon: LayoutDashboard },
  { label: "Workflows", icon: Workflow },
  { label: "Executions", icon: Activity },
  { label: "AI Logs", icon: Bot },
  { label: "Documents", icon: FileText },
  { label: "Alerts", icon: Bell }
];

export function Sidebar() {
  return (
    <aside className="hidden min-h-screen w-64 border-r border-line bg-white px-4 py-5 lg:block">
      <div className="mb-7 flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded bg-ink text-white">
          <Workflow size={18} aria-hidden="true" />
        </div>
        <div>
          <p className="text-sm font-semibold text-ink">AI Workflow</p>
          <p className="text-xs text-slate-500">Automation Ops</p>
        </div>
      </div>
      <nav className="space-y-1">
        {items.map((item, index) => {
          const Icon = item.icon;
          return (
            <button
              key={item.label}
              className={`flex h-10 w-full items-center gap-3 rounded px-3 text-left text-sm ${
                index === 0 ? "bg-panel font-semibold text-ink" : "text-slate-600 hover:bg-panel"
              }`}
              title={item.label}
            >
              <Icon size={17} aria-hidden="true" />
              {item.label}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}

