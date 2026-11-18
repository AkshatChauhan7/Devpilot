import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  Repository,
  Installation,
  Task,
  Execution,
  PullRequest,
  PaginatedResponse,
  GitHubRepository,
  GitHubFile,
  GitHubBranch,
  GitHubCommit,
} from "@/types";

type QueryKey = readonly unknown[];

export function useRepositories(params?: {
  page?: number;
  page_size?: number;
  search?: string;
  language?: string;
  installation_id?: number;
}) {
  return useQuery<PaginatedResponse<Repository>>({
    queryKey: ["repositories", params],
    queryFn: () => api.getRepositories(params),
  });
}

export function useRepository(repoId: number, options?: UseQueryOptions<Repository>) {
  return useQuery<Repository>({
    queryKey: ["repository", repoId],
    queryFn: () => api.getRepository(repoId),
    enabled: !!repoId,
    ...options,
  });
}

export function useInstallations(params?: { page?: number; page_size?: number }) {
  return useQuery<PaginatedResponse<Installation>>({
    queryKey: ["installations", params],
    queryFn: () => api.getInstallations(params),
  });
}

export function useInstallation(installationId: number) {
  return useQuery<Installation>({
    queryKey: ["installation", installationId],
    queryFn: () => api.getInstallation(installationId),
    enabled: !!installationId,
  });
}

export function useTasks(params?: {
  page?: number;
  page_size?: number;
  status?: string;
  type?: string;
  repository_id?: number;
}) {
  return useQuery<PaginatedResponse<Task>>({
    queryKey: ["tasks", params],
    queryFn: () => api.getTasks(params),
  });
}

export function useTask(taskId: number, options?: UseQueryOptions<Task>) {
  return useQuery<Task>({
    queryKey: ["task", taskId],
    queryFn: () => api.getTask(taskId),
    enabled: !!taskId,
    refetchInterval: (data) => (data?.status === "running" || data?.status === "queued" ? 2000 : false),
    ...options,
  });
}

export function useExecutions(params?: {
  page?: number;
  page_size?: number;
  status?: string;
  task_id?: number;
  repository_id?: number;
}) {
  return useQuery<PaginatedResponse<Execution>>({
    queryKey: ["executions", params],
    queryFn: () => api.getExecutions(params),
  });
}

export function useExecution(executionId: number) {
  return useQuery<Execution>({
    queryKey: ["execution", executionId],
    queryFn: () => api.getExecution(executionId),
    enabled: !!executionId,
    refetchInterval: (data) => (data?.status === "running" || data?.status === "preparing" ? 2000 : false),
  });
}

export function usePullRequests(params?: {
  page?: number;
  page_size?: number;
  status?: string;
  repository_id?: number;
  task_id?: number;
}) {
  return useQuery<PaginatedResponse<PullRequest>>({
    queryKey: ["pull-requests", params],
    queryFn: () => api.getPullRequests(params),
  });
}

export function usePullRequest(prId: number) {
  return useQuery<PullRequest>({
    queryKey: ["pull-request", prId],
    queryFn: () => api.getPullRequest(prId),
    enabled: !!prId,
  });
}

// Mutations
export function useCreateRepository() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { github_id: number; installation_id?: number }) => api.createRepository(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repositories"] });
    },
  });
}

export function useSyncRepositories() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (installationId: number) => api.syncRepositories(installationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repositories"] });
    },
  });
}

export function useAnalyzeRepository() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (repoId: number) => api.analyzeRepository(repoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repositories"] });
    },
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      type: string;
      title: string;
      description?: string;
      input_data?: Record<string, any>;
      repository_id?: number;
    }) => api.createTask(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}

export function useCancelTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (taskId: number) => api.cancelTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}

export function useCreateExecution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      command: string;
      working_directory?: string;
      image: string;
      environment?: Record<string, string>;
      timeout?: number;
      task_id?: number;
      repository_id?: number;
    }) => api.createExecution(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["executions"] });
    },
  });
}

export function useCancelExecution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (executionId: number) => api.cancelExecution(executionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["executions"] });
    },
  });
}

export function useCreatePullRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      title: string;
      body?: string;
      head_branch: string;
      base_branch?: string;
      is_draft?: boolean;
      review_required?: boolean;
      repository_id: number;
      task_id?: number;
    }) => api.createPullRequest(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pull-requests"] });
    },
  });
}

export function useMergePullRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ prId, mergeMethod }: { prId: number; mergeMethod?: string }) =>
      api.mergePullRequest(prId, mergeMethod),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pull-requests"] });
    },
  });
}

export function useClosePullRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (prId: number) => api.closePullRequest(prId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pull-requests"] });
    },
  });
}

// GitHub
export function useGitHubRepositories(installationId?: number) {
  return useQuery<GitHubRepository[]>({
    queryKey: ["github-repositories", installationId],
    queryFn: () => api.getGitHubRepositories(installationId),
    enabled: !!installationId,
  });
}

export function useRepositoryContents(
  owner: string,
  repo: string,
  path?: string,
  ref?: string,
  installationId?: number
) {
  return useQuery<GitHubFile[]>({
    queryKey: ["github-contents", owner, repo, path, ref, installationId],
    queryFn: () => api.getRepositoryContents(owner, repo, path, ref, installationId),
    enabled: !!owner && !!repo,
  });
}

export function useBranches(owner: string, repo: string, installationId?: number) {
  return useQuery<GitHubBranch[]>({
    queryKey: ["github-branches", owner, repo, installationId],
    queryFn: () => api.listBranches(owner, repo, installationId),
    enabled: !!owner && !!repo,
  });
}

export function useCommits(
  owner: string,
  repo: string,
  params?: { sha?: string; path?: string; per_page?: number },
  installationId?: number
) {
  return useQuery<GitHubCommit[]>({
    queryKey: ["github-commits", owner, repo, params, installationId],
    queryFn: () => api.listCommits(owner, repo, params, installationId),
    enabled: !!owner && !!repo,
  });
}