"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Loader2, Zap, Bug, FileCode, FlaskConical, GitPullRequest, Package, Shield } from "lucide-react";
import { useTasks, useCreateTask } from "@/hooks/useApi";
import { useRepositories } from "@/hooks/useApi";
import { cn } from "@/lib/utils";
import Link from "next/link";

const taskTypes = [
  { value: "repository_analysis", label: "Repository Analysis", icon: Zap },
  { value: "bug_detection", label: "Bug Detection", icon: Bug },
  { value: "code_generation", label: "Code Generation", icon: FileCode },
  { value: "code_modification", label: "Code Modification", icon: FileCode },
  { value: "test_generation", label: "Test Generation", icon: FlaskConical },
  { value: "test_execution", label: "Test Execution", icon: FlaskConical },
  { value: "pr_creation", label: "Pull Request Creation", icon: GitPullRequest },
  { value: "dependency_update", label: "Dependency Update", icon: Package },
  { value: "security_scan", label: "Security Scan", icon: Shield },
];

const statusOptions = [
  { value: "", label: "All Statuses" },
  { value: "pending", label: "Pending" },
  { value: "queued", label: "Queued" },
  { value: "running", label: "Running" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "cancelled", label: "Cancelled" },
];

export default function TasksPage() {
  const [status, setStatus] = useState("");
  const [type, setType] = useState("");
  const [repositoryId, setRepositoryId] = useState("");
  const [page, setPage] = useState(1);
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    type: "bug_detection",
    title: "",
    description: "",
    repository_id: "",
  });

  const { data: tasksData, isLoading, refetch } = useTasks({
    page,
    page_size: 20,
    status: status || undefined,
    type: type || undefined,
    repository_id: repositoryId ? parseInt(repositoryId) : undefined,
  });

  const { data: reposData } = useRepositories({ page_size: 100 });
  const createTask = useCreateTask();

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await createTask.mutateAsync({
      type: createForm.type as any,
      title: createForm.title,
      description: createForm.description,
      repository_id: createForm.repository_id ? parseInt(createForm.repository_id) : undefined,
    });
    setShowCreate(false);
    setCreateForm({ type: "bug_detection", title: "", description: "", repository_id: "" });
    refetch();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "running":
      case "queued":
        return "success";
      case "completed":
        return "default";
      case "failed":
        return "destructive";
      case "cancelled":
        return "secondary";
      default:
        return "warning";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Tasks</h1>
          <p className="text-muted-foreground">Manage and monitor your automation tasks</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Task
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <Select
              value={status}
              onValueChange={setStatus}
              options={statusOptions}
              placeholder="Status"
            />
            <Select
              value={type}
              onValueChange={setType}
              options={[{ value: "", label: "All Types" }, ...taskTypes.map((t) => ({ value: t.value, label: t.label }))]}
              placeholder="Type"
            />
            <Select
              value={repositoryId}
              onValueChange={(v) => { setRepositoryId(v); setPage(1); }}
              options={[
                { value: "", label: "All Repositories" },
                ...(reposData?.items.map((r) => ({ value: String(r.id), label: r.full_name })) || []),
              ]}
              placeholder="Repository"
            />
          </div>
        </CardContent>
      </Card>

      {/* Task List */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : tasksData?.items.length === 0 ? (
            <div className="text-center py-16">
              <Zap className="h-16 w-16 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">No tasks found</h3>
              <p className="text-muted-foreground mb-4">Create a task to get started</p>
              <Button onClick={() => setShowCreate(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create Task
              </Button>
            </div>
          ) : (
            <>
              <div className="divide-y">
                {tasksData?.items.map((task) => (
                  <div key={task.id} className="p-4 hover:bg-accent/50 transition-colors">
                    <Link href={`/tasks/${task.id}`} className="flex items-start justify-between gap-4 w-full">
                      <div className="flex items-center gap-4 min-w-0 flex-1">
                        <div className={cn("h-2 w-2 rounded-full mt-2 flex-shrink-0", task.status === "running" && "bg-green-500 animate-pulse", task.status === "completed" && "bg-green-500", task.status === "failed" && "bg-red-500", task.status === "pending" && "bg-yellow-500", task.status === "queued" && "bg-blue-500")} />
                        <div className="min-w-0">
                          <Link href={`/tasks/${task.id}`} className="font-medium truncate block hover:text-primary transition-colors">
                            {task.title}
                          </Link>
                          <p className="text-sm text-muted-foreground truncate max-w-md">{task.description || "No description"}</p>
                          <div className="flex items-center gap-3 mt-1 flex-wrap">
                            <Badge variant="outline" className="text-xs capitalize">{task.type.replace("_", " ")}</Badge>
                            <Badge variant={getStatusBadge(task.status)}>{task.status}</Badge>
                            {task.repository_id && reposData?.items.find((r) => r.id === task.repository_id) && (
                              <span className="text-xs text-muted-foreground">{reposData.items.find((r) => r.id === task.repository_id)?.full_name}</span>
                            )}
                            <span className="text-xs text-muted-foreground">Progress: {task.progress}%</span>
                          </div>
                          {task.error_message && (
                            <p className="text-sm text-destructive mt-1 truncate max-w-md">{task.error_message}</p>
                          )}
                        </div>
                      </div>
                      {task.status === "running" || task.status === "queued" || task.status === "pending" ? (
                        <Button variant="ghost" size="icon" onClick={() => {}} disabled>
                          <Loader2 className="h-4 w-4 animate-spin" />
                        </Button>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {tasksData && tasksData.total_pages > 1 && (
                <div className="flex items-center justify-between p-4 border-t">
                  <p className="text-sm text-muted-foreground">
                    Page {tasksData.page} of {tasksData.total_pages} ({tasksData.total} total)
                  </p>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={tasksData.page === 1}>
                      Previous
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(tasksData.total_pages, p + 1))} disabled={tasksData.page === tasksData.total_pages}>
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Create Task Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>Create New Task</CardTitle>
            </CardHeader>
            <form onSubmit={handleCreate} className="p-4 space-y-4">
              <Select
                label="Task Type"
                value={createForm.type}
                onValueChange={(v) => setCreateForm({ ...createForm, type: v })}
                options={taskTypes.map((t) => ({ value: t.value, label: t.label }))}
                placeholder="Select type"
              />
              <Input
                label="Title"
                value={createForm.title}
                onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                placeholder="Enter task title"
                required
              />
              <Input
                label="Description"
                value={createForm.description}
                onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                placeholder="Optional description"
              />
              <Select
                label="Repository (optional)"
                value={createForm.repository_id}
                onValueChange={(v) => setCreateForm({ ...createForm, repository_id: v })}
                options={[
                  { value: "", label: "No repository" },
                  ...(reposData?.items.map((r) => ({ value: String(r.id), label: r.full_name })) || []),
                ]}
                placeholder="Select repository"
              />
              <div className="flex gap-2 pt-4">
                <Button type="submit" className="flex-1" disabled={createTask.isPending}>
                  {createTask.isPending ? "Creating..." : "Create Task"}
                </Button>
                <Button type="button" variant="outline" className="flex-1" onClick={() => setShowCreate(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}