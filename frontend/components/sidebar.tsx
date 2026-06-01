"use client";

import { Activity, Bell, Bot, FileText, LayoutDashboard, LogOut, User, Workflow } from "lucide-react";
import { useAuth } from "@/context/auth-context";

const items = [
  { label: "Dashboard", icon: LayoutDashboard },
  { label: "Workflows", icon: Workflow },
  { label: "Executions", icon: Activity },
  { label: "AI Logs", icon: Bot },
  { label: "Documents", icon: FileText },
  { label: "Alerts", icon: Bell }
];

export function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <aside className="hidden min-h-screen w-64 border-r border-line bg-white px-4 py-5 lg:flex flex-col justify-between">
      <div>
        <div className="mb-7 flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded bg-ink text-white shadow-md transition-transform hover:scale-105">
            <Workflow size={18} aria-hidden="true" />
          </div>
          <div>
            <p className="text-sm font-semibold text-ink leading-none">AI Workflow</p>
            <p className="text-[11px] text-slate-500 mt-1">Automation Ops</p>
          </div>
        </div>

        <nav className="space-y-1">
          {items.map((item, index) => {
            const Icon = item.icon;
            return (
              <button
                key={item.label}
                className={`flex h-10 w-full items-center gap-3 rounded px-3 text-left text-sm transition-all duration-200 ${
                  index === 0 
                    ? "bg-panel font-semibold text-ink shadow-sm" 
                    : "text-slate-600 hover:bg-panel hover:translate-x-1"
                }`}
                title={item.label}
              >
                <Icon size={17} aria-hidden="true" />
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>

      {user && (
        <div className="mt-auto border-t border-line pt-4 space-y-3">
          <div className="flex items-center gap-3 px-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-panel border border-line text-ink">
              <User size={18} aria-hidden="true" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-ink truncate leading-tight">{user.name}</p>
              <p className="text-[10px] text-slate-400 truncate mt-0.5">{user.email}</p>
            </div>
            <span className="inline-flex items-center rounded-full bg-teal-50 px-2 py-0.5 text-[9px] font-medium text-teal-800 border border-teal-100 uppercase">
              {user.role}
            </span>
          </div>

          <button
            onClick={logout}
            className="flex h-10 w-full items-center gap-3 rounded px-3 text-left text-sm text-red-600 hover:bg-red-50 hover:text-red-700 transition-colors duration-200"
            title="Sign out"
          >
            <LogOut size={17} aria-hidden="true" />
            <span>Sign out</span>
          </button>
        </div>
      )}
    </aside>
  );
}
