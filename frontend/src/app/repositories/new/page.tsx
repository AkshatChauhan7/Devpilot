"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Github, Loader2, ArrowLeft, CheckCircle, AlertCircle } from "lucide-react";
import { useRepositories, useGitHubRepositories, useInstallations } from "@/hooks/useApi";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import Link from "next/link";

export default function NewRepositoryPage() {
  const router = useRouter();
  const [selectedInstallation, setSelectedInstallation] = useState("");
  const [selectedRepos, setSelectedRepos] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [creating, setCreating] = useState(false);

  const { data: installationsData } = useInstallations();
  const { data: githubReposData, isLoading: loadingRepos, refetch: refetchRepos } = useGitHubRepositories(
    selectedInstallation ? parseInt(selectedInstallation) : undefined
  );
  const createRepository = useRepositories();

  const handleInstallationChange = (id: string) => {
    setSelectedInstallation(id);
    setSelectedRepos([]);
    refetchRepos();
  };

  const toggleRepo = (repoId: number) => {
    const id = String(repoId);
    setSelectedRepos((prev) => prev.includes(id) ? prev.filter((r) => r !== id) : [...prev, id]);
  };

  const handleCreate = async () => {
    if (selectedRepos.length === 0) return;
    setCreating(true);
    try {
      for (const repoId of selectedRepos) {
        await createRepository.mutateAsync({
          github_id: parseInt(repoId),
          installation_id: selectedInstallation ? parseInt(selectedInstallation) : undefined,
        });
      }
      router.push("/repositories");
    } finally {
      setCreating(false);
    }
  };

  const filteredRepos = githubReposData?.filter((repo) =>
    repo.full_name.toLowerCase().includes(search.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Add Repository</h1>
          <p className="text-muted-foreground">Select repositories from your GitHub installations</p>
        </div>
      </div>

      {/* Installation Selector */}
      <Card>
        <CardHeader>
          <CardTitle>Select Installation</CardTitle>
        </CardHeader>
        <CardContent>
          {installationsData?.items.length === 0 ? (
            <div className="text-center py-8">
              <Github className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground mb-4">No GitHub installations found</p>
              <p className="text-sm text-muted-foreground">Install the DevPilot GitHub App on your account or organization</p>
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {installationsData.items.map((installation) => (
                <Button
                  key={installation.id}
                  variant={selectedInstallation === String(installation.id) ? "default" : "outline"}
                  className="w-full justify-start gap-3"
                  onClick={() => handleInstallationChange(String(installation.id))}
                >
                  <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    {installation.account_avatar_url ? (
                      <img src={installation.account_avatar_url} alt="" className="h-10 w-10 rounded-full" />
                    ) : (
                      <span className="text-primary font-bold">{installation.account_login[0]}</span>
                    )}
                  </div>
                  <div className="text-left">
                    <p className="font-medium">{installation.account_login}</p>
                    <p className="text-xs text-muted-foreground capitalize">{installation.account_type}</p>
                  </div>
                  {selectedInstallation === String(installation.id) && (
                    <CheckCircle className="h-5 w-5 text-primary ml-auto" />
                  )}
                </Button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Repository List */}
      {selectedInstallation && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Available Repositories</CardTitle>
            <div className="flex items-center gap-2">
              <Input
                placeholder="Search repositories..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-64"
              />
              <span className="text-sm text-muted-foreground">
                {selectedRepos.length} selected
              </span>
            </div>
          </CardHeader>
          <CardContent>
            {loadingRepos ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
            ) : filteredRepos.length === 0 ? (
              <div className="text-center py-12">
                <Github className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-muted-foreground">No repositories found</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-[500px] overflow-y-auto">
                {filteredRepos.map((repo) => (
                  <Button
                    key={repo.id}
                    variant={selectedRepos.includes(String(repo.id)) ? "default" : "outline"}
                    className="w-full justify-start gap-3"
                    onClick={() => toggleRepo(repo.id)}
                  >
                    <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                      <Github className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div className="text-left flex-1 min-w-0">
                      <p className="font-medium truncate">{repo.full_name}</p>
                      <p className="text-xs text-muted-foreground truncate">{repo.description || "No description"}</p>
                      <div className="flex items-center gap-2 mt-1">
                        {repo.language && <Badge variant="outline" className="text-xs">{repo.language}</Badge>}
                        <Badge variant="outline" className="text-xs">★ {repo.stargazers_count}</Badge>
                        {repo.private && <Badge variant="secondary" className="text-xs">Private</Badge>}
                      </div>
                    </div>
                    {selectedRepos.includes(String(repo.id)) && (
                      <CheckCircle className="h-5 w-5 text-primary" />
                    )}
                  </Button>
                ))}
              </div>
            )}
          </CardContent>
          <CardFooter className="flex justify-end p-4 border-t">
            <Button variant="outline" onClick={() => router.back()}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <Button onClick={handleCreate} disabled={selectedRepos.length === 0 || creating} loading={creating}>
              {creating ? "Adding..." : `Add ${selectedRepos.length} Repository${selectedRepos.length > 1 ? "s" : ""}`}
            </Button>
          </CardFooter>
        </Card>
      )}
    </div>
  );
}

import { CardFooter } from "@/components/ui/card";