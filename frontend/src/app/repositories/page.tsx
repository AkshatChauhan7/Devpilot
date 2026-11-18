"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Search, Filter, GitBranch, Loader2, RefreshCw } from "lucide-react";
import { useRepositories, useInstallations, useSyncRepositories, useAnalyzeRepository } from "@/hooks/useApi";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import Link from "next/link";

export default function RepositoriesPage() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [language, setLanguage] = useState("");
  const [installationId, setInstallationId] = useState("");
  const [page, setPage] = useState(1);

  const { data: reposData, isLoading, refetch } = useRepositories({
    page,
    page_size: 20,
    search: search || undefined,
    language: language || undefined,
    installation_id: installationId ? parseInt(installationId) : undefined,
  });

  const { data: installationsData } = useInstallations();
  const syncRepositories = useSyncRepositories();
  const analyzeRepository = useAnalyzeRepository();

  const languages = [
    "Python",
    "JavaScript",
    "TypeScript",
    "Go",
    "Rust",
    "Java",
    "C++",
    "C#",
    "Ruby",
    "PHP",
  ];

  const handleSync = async (id: number) => {
    await syncRepositories.mutateAsync(id);
    refetch();
  };

  const handleAnalyze = async (repoId: number) => {
    await analyzeRepository.mutateAsync(repoId);
    refetch();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Repositories</h1>
          <p className="text-muted-foreground">Manage and analyze your GitHub repositories</p>
        </div>
        <Button asChild>
          <Link href="/repositories/new">
            <Plus className="mr-2 h-4 w-4" />
            Add Repository
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search repositories..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && setPage(1)}
                className="pl-10"
              />
            </div>
            <Select
              value={language}
              onValueChange={setLanguage}
              options={[{ value: "", label: "All Languages" }, ...languages.map((l) => ({ value: l, label: l }))]}
              placeholder="Language"
            />
            <Select
              value={installationId}
              onValueChange={(v) => { setInstallationId(v); setPage(1); }}
              options={[
                { value: "", label: "All Installations" },
                ...(installationsData?.items.map((i) => ({ value: String(i.id), label: i.account_login })) || []),
              ]}
              placeholder="Installation"
            />
            {installationsData && installationsData.items.length > 0 && (
              <Button variant="outline" onClick={() => handleSync(parseInt(installationId || installationsData.items[0].id))} disabled={syncRepositories.isPending}>
                <RefreshCw className={cn("mr-2 h-4 w-4", syncRepositories.isPending && "animate-spin")} />
                Sync
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Repository List */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : reposData?.items.length === 0 ? (
            <div className="text-center py-16">
              <GitBranch className="h-16 w-16 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">No repositories found</h3>
              <p className="text-muted-foreground mb-4">Add a repository or sync from GitHub to get started</p>
              <Button asChild>
                <Link href="/repositories/new">
                  <Plus className="mr-2 h-4 w-4" />
                  Add Repository
                </Link>
              </Button>
            </div>
          ) : (
            <>
              <div className="divide-y">
                {reposData?.items.map((repo) => (
                  <div key={repo.id} className="p-4 hover:bg-accent/50 transition-colors">
                    <Link href={`/repositories/${repo.id}`} className="flex items-center justify-between w-full">
                      <div className="flex items-center gap-4 min-w-0">
                        <div className="h-12 w-12 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                          <GitBranch className="h-6 w-6 text-muted-foreground" />
                        </div>
                        <div className="min-w-0">
                          <Link href={`/repositories/${repo.id}`} className="font-medium truncate block hover:text-primary transition-colors">
                            {repo.full_name}
                          </Link>
                          <p className="text-sm text-muted-foreground truncate max-w-md">{repo.description || "No description"}</p>
                          <div className="flex items-center gap-3 mt-1">
                            {repo.language && <Badge variant="outline" className="text-xs">{repo.language}</Badge>}
                            <Badge variant="outline" className="text-xs capitalize">{repo.analysis_status}</Badge>
                            <span className="text-xs text-muted-foreground">★ {repo.stars}</span>
                            <span className="text-xs text-muted-foreground">⌵ {repo.forks}</span>
                            {repo.is_private && <Badge variant="secondary" className="text-xs">Private</Badge>}
                            {repo.is_archived && <Badge variant="destructive" className="text-xs">Archived</Badge>}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button variant="ghost" size="icon" onClick={() => handleAnalyze(repo.id)} disabled={analyzeRepository.isPending}>
                          <RefreshCw className={cn("h-4 w-4", analyzeRepository.isPending && "animate-spin")} />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {reposData && reposData.total_pages > 1 && (
                <div className="flex items-center justify-between p-4 border-t">
                  <p className="text-sm text-muted-foreground">
                    Page {reposData.page} of {reposData.total_pages} ({reposData.total} total)
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={reposData.page === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(reposData.total_pages, p + 1))}
                      disabled={reposData.page === reposData.total_pages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}