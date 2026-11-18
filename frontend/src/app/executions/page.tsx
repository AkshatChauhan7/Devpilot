"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Loader2, Terminal, Play, Stop, X } from "lucide-react";
import { useExecutions, useCreateExecution } from "@/hooks/useApi";
import { useTasks } from "@/hooks/useApi";
import { useRepositories } from "@/hooks/useApi";
import { cn } from "@/lib/utils";
import Link from "next/link";

const statusOptions = [
  { value: "", label: "All Statuses" },
  { value: "pending", label: "Pending" },
  { value: "queued", label: "Queued" },
  { value: "preparing", label: "Preparing" },
  { value: "running", label: "Running" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "timeout", label: "Timeout" },
  { value: "cancelled", label: "Cancelled" },
];

const commonImages = [
  "python:3.12-slim",
  "node:20-slim",
  "golang:1.22-alpine",
  "rust:1.78-slim",
  "openjdk:21-slim",
  "ubuntu:22.04",
];

export default function ExecutionsPage() {
  const [status, setStatus] = useState("");
  const [taskId, setTaskId] = useState("");
  const [repositoryId, setRepositoryId] = useState("");
  const [page, setPage] = useState(1);
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    command: "",
    working_directory: "/workspace",
    image: "python:3.12-slim",
    timeout: 300,
    task_id: "",
    repository_id: "",
  });

  const { data: executionsData, isLoading, refetch } = useExecutions({
    page,
    page_size: 20,
    status: status || undefined,
    task_id: taskId ? parseInt(taskId) : undefined,
    repository_id: repositoryId ? parseInt(repositoryId) : undefined,
  });

  const { data: tasksData } = useTasks({ page_size: 100, status: "completed" });
  const { data: reposData } = useRepositories({ page_size: 100 });
  const createExecution = useCreateExecution();

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await createExecution.mutateAsync({
      command: createForm.command,
      working_directory: createForm.working_directory,
      image: createForm.image,
      timeout: createForm.timeout,
      task_id: createForm.task_id ? parseInt(createForm.task_id) : undefined,
      repository_id: createForm.repository_id ? parseInt(createForm.repository_id) : undefined,
    });
    setShowCreate(false);
    setCreateForm({ command: "", working_directory: "/workspace", image: "python:3.12-slim", timeout: 300, task_id: "", repository_id: "" });
    refetch();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "running":
      case "preparing":
        return "success";
      case "completed":
        return "default";
      case "failed":
      case "timeout":
        return "destructive";
      case "cancelled":
        return "secondary";
      default:
        return "warning";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "running":
      case "preparing":
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case "completed":
        return <Terminal className="h-4 w-4 text-green-500" />;
      case "failed":
      case "timeout":
        return <X className="h-4 w-4 text-red-500" />;
      case "cancelled":
        return <Stop className="h-4 w-4" />;
      default:
        return <Play className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Executions</h1>
          <p className="text-muted-foreground">Monitor and manage code executions</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Execution
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
              value={taskId}
              onValueChange={(v) => { setTaskId(v); setPage(1); }}
              options={[
                { value: "", label: "All Tasks" },
                ...(tasksData?.items.map((t) => ({ value: String(t.id), label: t.title })) || []),
              ]}
              placeholder="Task"
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

      {/* Execution List */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : executionsData?.items.length === 0 ? (
            <div className="text-center py-16">
              <Terminal className="h-16 w-16 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">No executions found</h3>
              <p className="text-muted-foreground mb-4">Create an execution to run code in isolated containers</p>
              <Button onClick={() => setShowCreate(true)}>
                <Plus className="mr-2 h-4 w-4" />
                New Execution
              </Button>
            </div>
          ) : (
            <>
              <div className="divide-y">
                {executionsData?.items.map((execution) => (
                  <div key={execution.id} className="p-4 hover:bg-accent/50 transition-colors">
                    <Link href={`/executions/${execution.id}`} className="flex items-center justify-between gap-4 w-full">
                      <div className="flex items-center gap-4 min-w-0 flex-1">
                        <div className="flex-shrink-0">{getStatusIcon(execution.status)}</div>
                        <div className="min-w-0">
                          <Link href={`/executions/${execution.id}`} className="font-medium truncate block hover:text-primary transition-colors font-mono text-sm">
                            {execution.command.length > 80 ? execution.command.slice(0, 80) + "..." : execution.command}
                          </Link>
                          <div className="flex items-center gap-3 mt-1 flex-wrap text-xs text-muted-foreground">
                            <Badge variant="outline">{execution.image}</Badge>
                            {execution.task_id && tasksData?.items.find((t) => t.id === execution.task_id) && (
                              <span>Task: {tasksData.items.find((t) => t.id === execution.task_id)?.title}</span>
                            )}
                            {execution.repository_id && reposData?.items.find((r) => r.id === execution.repository_id) && (
                              <span>Repo: {reposData.items.find((r) => r.id === execution.repository_id)?.full_name}</span>
                            )}
                            {execution.duration_ms && <span>{(execution.duration_ms / 1000).toFixed(1)}s</span>}
                            {execution.exit_code !== null && execution.exit_code !== undefined && (
                              <span>Exit: {execution.exit_code}</span>
                            )}
                          </div>
                          {execution.error_message && (
                            <p className="text-sm text-destructive mt-1 truncate max-w-md">{execution.error_message}</p>
                          )}
                        </div>
                      </div>
                      <Badge variant={getStatusBadge(execution.status)}>{execution.status}</Badge>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {executionsData && executionsData.total_pages > 1 && (
                <div className="flex items-center justify-between p-4 border-t">
                  <p className="text-sm text-muted-foreground">
                    Page {executionsData.page} of {executionsData.total_pages} ({executionsData.total} total)
                  </p>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={executionsData.page === 1}>
                      Previous
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(executionsData.total_pages, p + 1))} disabled={executionsData.page === executionsData.total_pages}>
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Create Execution Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>New Execution</CardTitle>
            </CardHeader>
            <form onSubmit={handleCreate} className="p-4 space-y-4">
              <Input
                label="Command"
                value={createForm.command}
                onChange={(e) => setCreateForm({ ...createForm, command: e.target.value })}
                placeholder="e.g., python script.py, npm test, go test ./..."
                required
              />
              <Input
                label="Working Directory"
                value={createForm.working_directory}
                onChange={(e) => setCreateForm({ ...createForm, working_directory: e.target.value })}
                placeholder="/workspace"
              />
              <Select
                label="Docker Image"
                value={createForm.image}
                onValueChange={(v) => setCreateForm({ ...createForm, image: v })}
                options={commonImages.map((i) => ({ value: i, label: i }))}
                placeholder="Select image"
              />
              <Input
                label="Timeout (seconds)"
                type="number"
                value={String(createForm.timeout)}
                onChange={(e) => setCreateForm({ ...createForm, timeout: parseInt(e.target.value) || 300 })}
                placeholder="300"
              />
              <Select
                label="Task (optional)"
                value={createForm.task_id}
                onValueChange={(v) => setCreateForm({ ...createForm, task_id: v })}
                options={[
                  { value: "", label: "No task" },
                  ...(tasksData?.items.map((t) => ({ value: String(t.id), label: t.title })) || []),
                ]}
                placeholder="Select task"
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
                <Button type="submit" className="flex-1" disabled={createExecution.isPending}>
                  {createExecution.isPending ? "Creating..." : "Create Execution"}
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