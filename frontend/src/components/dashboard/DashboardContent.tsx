"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Plus, GitBranch, Zap, Terminal, GitPullRequest, ArrowRight, Clock, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { useRepositories } from "@/hooks/useApi";
import { useTasks } from "@/hooks/useApi";
import { useExecutions } from "@/hooks/useApi";
import { usePullRequests } from "@/hooks/useApi";
import { formatRelativeTime } from "@/lib/utils";
import Link from "next/link";

const statCards = [
  {
    name: "Repositories",
    href: "/repositories",
    icon: GitBranch,
    color: "text-blue-500",
    bg: "bg-blue-500/10",
  },
  {
    name: "Active Tasks",
    href: "/tasks",
    icon: Zap,
    color: "text-purple-500",
    bg: "bg-purple-500/10",
  },
  {
    name: "Executions",
    href: "/executions",
    icon: Terminal,
    color: "text-orange-500",
    bg: "bg-orange-500/10",
  },
  {
    name: "Pull Requests",
    href: "/pull-requests",
    icon: GitPullRequest,
    color: "text-green-500",
    bg: "bg-green-500/10",
  },
];

function StatCard({ name, count, href, icon: Icon, color, bg }: any) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{name}</p>
            <p className="text-3xl font-bold mt-1">{count}</p>
          </div>
          <Link href={href} className={cn(`${bg} ${color} p-3 rounded-lg hover:opacity-80 transition-opacity`)}>
            <Icon className="h-6 w-6" />
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

export function DashboardContent() {
  const { data: reposData } = useRepositories({ page_size: 5 });
  const { data: tasksData } = useTasks({ page_size: 10, status: "running" });
  const { data: executionsData } = useExecutions({ page_size: 10, status: "running" });
  const { data: prsData } = usePullRequests({ page_size: 10, status: "open" });

  const activeTasks = tasksData?.items.filter((t) => t.status === "running").length || 0;
  const runningExecutions = executionsData?.items.filter((e) => e.status === "running").length || 0;
  const openPRs = prsData?.items.filter((p) => p.status === "open").length || 0;

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Overview of your development automation</p>
        </div>
        <Button asChild>
          <Link href="/repositories/new">
            <Plus className="mr-2 h-4 w-4" />
            Add Repository
          </Link>
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          name="Repositories"
          count={reposData?.total || 0}
          href="/repositories"
          icon={GitBranch}
          color="text-blue-500"
          bg="bg-blue-500/10"
        />
        <StatCard
          name="Active Tasks"
          count={activeTasks}
          href="/tasks"
          icon={Zap}
          color="text-purple-500"
          bg="bg-purple-500/10"
        />
        <StatCard
          name="Running Executions"
          count={runningExecutions}
          href="/executions"
          icon={Terminal}
          color="text-orange-500"
          bg="bg-orange-500/10"
        />
        <StatCard
          name="Open PRs"
          count={openPRs}
          href="/pull-requests"
          icon={GitPullRequest}
          color="text-green-500"
          bg="bg-green-500/10"
        />
      </div>

      {/* Recent Activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Tasks */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Tasks</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/tasks">View all <ArrowRight className="ml-1 h-4 w-4" /></Link>
            </Button>
          </CardHeader>
          <CardContent>
            {tasksData?.items.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Zap className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No recent tasks</p>
                <Button variant="link" asChild className="mt-2">
                  <Link href="/tasks/new">Create a task</Link>
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {tasksData?.items.slice(0, 5).map((task) => (
                  <div key={task.id} className="flex items-center justify-between py-2 border-b last:border-0">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className={cn("h-2 w-2 rounded-full", task.status === "running" && "bg-green-500 animate-pulse", task.status === "completed" && "bg-green-500", task.status === "failed" && "bg-red-500", task.status === "pending" && "bg-yellow-500")} />
                      <div>
                        <p className="font-medium truncate max-w-[200px]">{task.title}</p>
                        <p className="text-xs text-muted-foreground">{formatRelativeTime(task.created_at)}</p>
                      </div>
                    </div>
                    <Badge variant={task.status === "running" ? "success" : task.status === "completed" ? "default" : task.status === "failed" ? "destructive" : "warning"}>
                      {task.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Executions */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Executions</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/executions">View all <ArrowRight className="ml-1 h-4 w-4" /></Link>
            </Button>
          </CardHeader>
          <CardContent>
            {executionsData?.items.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Terminal className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No recent executions</p>
              </div>
            ) : (
              <div className="space-y-3">
                {executionsData?.items.slice(0, 5).map((execution) => (
                  <div key={execution.id} className="flex items-center justify-between py-2 border-b last:border-0">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className={cn("h-2 w-2 rounded-full", execution.status === "running" && "bg-green-500 animate-pulse", execution.status === "completed" && "bg-green-500", execution.status === "failed" && "bg-red-500")} />
                      <div>
                        <p className="font-medium truncate max-w-[200px] font-mono text-sm">{execution.command.slice(0, 50)}</p>
                        <p className="text-xs text-muted-foreground">{formatRelativeTime(execution.created_at)}</p>
                      </div>
                    </div>
                    <Badge variant={execution.status === "running" ? "success" : execution.status === "completed" ? "default" : "destructive"}>
                      {execution.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Repositories */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Repositories</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/repositories">View all <ArrowRight className="ml-1 h-4 w-4" /></Link>
            </Button>
          </CardHeader>
          <CardContent>
            {reposData?.items.length === 0 ? (
              <div className="text-center py-12">
                <GitBranch className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium mb-2">No repositories yet</h3>
                <p className="text-muted-foreground mb-4">Connect your GitHub account and add repositories to get started</p>
                <Button asChild>
                  <Link href="/repositories/new">
                    <Plus className="mr-2 h-4 w-4" />
                    Add Repository
                  </Link>
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {reposData?.items.slice(0, 8).map((repo) => (
                  <Link key={repo.id} href={`/repositories/${repo.id}`} className="flex items-center justify-between p-3 rounded-lg hover:bg-accent transition-colors group">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
                        <GitBranch className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium truncate">{repo.full_name}</p>
                        <p className="text-sm text-muted-foreground truncate">{repo.description || "No description"}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {repo.language && <Badge variant="outline" className="text-xs">{repo.language}</Badge>}
                      <Badge variant="outline" className="text-xs">
                        {repo.analysis_status}
                      </Badge>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

import { cn } from "@/lib/utils";