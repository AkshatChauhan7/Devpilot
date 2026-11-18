"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Loader2, GitPullRequest, GitMerge, X, CheckCircle, Clock } from "lucide-react";
import { usePullRequests, useCreatePullRequest, useMergePullRequest, useClosePullRequest } from "@/hooks/useApi";
import { useRepositories } from "@/hooks/useApi";
import { useTasks } from "@/hooks/useApi";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { formatRelativeTime } from "@/lib/utils";

const statusOptions = [
  { value: "", label: "All Statuses" },
  { value: "draft", label: "Draft" },
  { value: "open", label: "Open" },
  { value: "closed", label: "Closed" },
  { value: "merged", label: "Merged" },
  { value: "failed", label: "Failed" },
];

export default function PullRequestsPage() {
  const [status, setStatus] = useState("");
  const [repositoryId, setRepositoryId] = useState("");
  const [taskId, setTaskId] = useState("");
  const [page, setPage] = useState(1);
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    title: "",
    body: "",
    head_branch: "",
    base_branch: "main",
    is_draft: true,
    review_required: true,
    repository_id: "",
    task_id: "",
  });

  const { data: prsData, isLoading, refetch } = usePullRequests({
    page,
    page_size: 20,
    status: status || undefined,
    repository_id: repositoryId ? parseInt(repositoryId) : undefined,
    task_id: taskId ? parseInt(taskId) : undefined,
  });

  const { data: reposData } = useRepositories({ page_size: 100 });
  const { data: tasksData } = useTasks({ page_size: 100, status: "completed" });
  const createPR = useCreatePullRequest();
  const mergePR = useMergePullRequest();
  const closePR = useClosePullRequest();

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await createPR.mutateAsync({
      title: createForm.title,
      body: createForm.body,
      head_branch: createForm.head_branch,
      base_branch: createForm.base_branch,
      is_draft: createForm.is_draft,
      review_required: createForm.review_required,
      repository_id: parseInt(createForm.repository_id),
      task_id: createForm.task_id ? parseInt(createForm.task_id) : undefined,
    });
    setShowCreate(false);
    setCreateForm({ title: "", body: "", head_branch: "", base_branch: "main", is_draft: true, review_required: true, repository_id: "", task_id: "" });
    refetch();
  };

  const handleMerge = async (prId: number) => {
    await mergePR.mutateAsync({ prId, mergeMethod: "merge" });
    refetch();
  };

  const handleClose = async (prId: number) => {
    await closePR.mutateAsync(prId);
    refetch();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "open":
        return "success";
      case "merged":
        return "default";
      case "closed":
        return "secondary";
      case "failed":
        return "destructive";
      default:
        return "warning";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "open":
        return <GitPullRequest className="h-4 w-4 text-green-500" />;
      case "merged":
        return <GitMerge className="h-4 w-4 text-purple-500" />;
      case "closed":
        return <X className="h-4 w-4 text-gray-500" />;
      case "failed":
        return <CheckCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Pull Requests</h1>
          <p className="text-muted-foreground">Manage and review pull requests</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create PR
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
              value={repositoryId}
              onValueChange={(v) => { setRepositoryId(v); setPage(1); }}
              options={[
                { value: "", label: "All Repositories" },
                ...(reposData?.items.map((r) => ({ value: String(r.id), label: r.full_name })) || []),
              ]}
              placeholder="Repository"
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
          </div>
        </CardContent>
      </Card>

      {/* PR List */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : prsData?.items.length === 0 ? (
            <div className="text-center py-16">
              <GitPullRequest className="h-16 w-16 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">No pull requests found</h3>
              <p className="text-muted-foreground mb-4">Create a pull request to propose changes</p>
              <Button onClick={() => setShowCreate(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create PR
              </Button>
            </div>
          ) : (
            <>
              <div className="divide-y">
                {prsData?.items.map((pr) => (
                  <div key={pr.id} className="p-4 hover:bg-accent/50 transition-colors">
                    <Link href={`/pull-requests/${pr.id}`} className="flex items-start justify-between gap-4 w-full">
                      <div className="flex items-center gap-4 min-w-0 flex-1">
                        <div className="flex-shrink-0">{getStatusIcon(pr.status)}</div>
                        <div className="min-w-0">
                          <Link href={`/pull-requests/${pr.id}`} className="font-medium truncate block hover:text-primary transition-colors">
                            #{pr.github_pr_number} {pr.title}
                          </Link>
                          <p className="text-sm text-muted-foreground truncate max-w-md">{pr.body?.slice(0, 100) || "No description"}</p>
                          <div className="flex items-center gap-3 mt-1 flex-wrap text-xs text-muted-foreground">
                            <Badge variant="outline">{pr.head_branch} → {pr.base_branch}</Badge>
                            <Badge variant={getStatusBadge(pr.status)}>{pr.status}</Badge>
                            {pr.repository_id && reposData?.items.find((r) => r.id === pr.repository_id) && (
                              <span>{reposData.items.find((r) => r.id === pr.repository_id)?.full_name}</span>
                            )}
                            {pr.files_changed !== undefined && <span>📁 {pr.files_changed} files</span>}
                            {pr.additions !== undefined && <span>+{pr.additions}</span>}
                            {pr.deletions !== undefined && <span>-{pr.deletions}</span>}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {pr.status === "open" && (
                          <>
                            <Button variant="ghost" size="icon" onClick={() => handleMerge(pr.id)} disabled={mergePR.isPending} title="Merge">
                              <GitMerge className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" onClick={() => handleClose(pr.id)} disabled={closePR.isPending} title="Close">
                              <X className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                        <Badge variant={getStatusBadge(pr.status)}>{pr.status}</Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {prsData && prsData.total_pages > 1 && (
                <div className="flex items-center justify-between p-4 border-t">
                  <p className="text-sm text-muted-foreground">
                    Page {prsData.page} of {prsData.total_pages} ({prsData.total} total)
                  </p>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={prsData.page === 1}>
                      Previous
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(prsData.total_pages, p + 1))} disabled={prsData.page === prsData.total_pages}>
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Create PR Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>Create Pull Request</CardTitle>
            </CardHeader>
            <form onSubmit={handleCreate} className="p-4 space-y-4">
              <Select
                label="Repository"
                value={createForm.repository_id}
                onValueChange={(v) => setCreateForm({ ...createForm, repository_id: v })}
                options={reposData?.items.map((r) => ({ value: String(r.id), label: r.full_name })) || []}
                placeholder="Select repository"
                required
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
              <Input
                label="Title"
                value={createForm.title}
                onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                placeholder="Pull request title"
                required
              />
              <Input
                label="Body"
                value={createForm.body}
                onChange={(e) => setCreateForm({ ...createForm, body: e.target.value })}
                placeholder="Pull request description"
              />
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Head Branch"
                  value={createForm.head_branch}
                  onChange={(e) => setCreateForm({ ...createForm, head_branch: e.target.value })}
                  placeholder="feature-branch"
                  required
                />
                <Input
                  label="Base Branch"
                  value={createForm.base_branch}
                  onChange={(e) => setCreateForm({ ...createForm, base_branch: e.target.value })}
                  placeholder="main"
                  required
                />
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={createForm.is_draft}
                    onChange={(e) => setCreateForm({ ...createForm, is_draft: e.target.checked })}
                    className="rounded border-input"
                  />
                  <span className="text-sm">Draft PR</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={createForm.review_required}
                    onChange={(e) => setCreateForm({ ...createForm, review_required: e.target.checked })}
                    className="rounded border-input"
                  />
                  <span className="text-sm">Require Review</span>
                </label>
              </div>
              <div className="flex gap-2 pt-4">
                <Button type="submit" className="flex-1" disabled={createPR.isPending}>
                  {createPR.isPending ? "Creating..." : "Create PR"}
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