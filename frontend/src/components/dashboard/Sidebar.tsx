"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  GitBranch,
  FileCode,
  Terminal,
  GitPullRequest,
  Settings,
  Bug,
  Zap,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useUIStore } from "@/lib/store";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Repositories", href: "/repositories", icon: GitBranch },
  { name: "Tasks", href: "/tasks", icon: Zap },
  { name: "Bug Detection", href: "/bugs", icon: Bug },
  { name: "Code Generation", href: "/generate", icon: FileCode },
  { name: "Executions", href: "/executions", icon: Terminal },
  { name: "Pull Requests", href: "/pull-requests", icon: GitPullRequest },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar({ user }: { user?: any }) {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 h-screen border-r bg-card transition-all duration-300",
        sidebarOpen ? "w-64" : "w-20"
      )}
    >
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center justify-between border-b px-4">
          {sidebarOpen && (
            <Link href="/" className="flex items-center gap-2 font-bold text-lg text-primary">
              <Zap className="h-6 w-6" />
              DevPilot
            </Link>
          )}
          <button
            onClick={toggleSidebar}
            className="flex h-10 w-10 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
            aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          >
            {sidebarOpen ? <ChevronLeft className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-3 overflow-y-auto" aria-label="Main navigation">
          {navigation.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                {sidebarOpen && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        {/* User */}
        <div className="border-t p-3">
          {sidebarOpen && user && (
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-medium">
                {user.name?.[0] || user.email?.[0] || "U"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user.name || user.email}</p>
                <p className="text-xs text-muted-foreground truncate">@{user.username || user.email?.split("@")[0]}</p>
              </div>
            </div>
          )}
          {!sidebarOpen && user && (
            <div className="flex justify-center">
              <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-medium">
                {user.name?.[0] || user.email?.[0] || "U"}
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}