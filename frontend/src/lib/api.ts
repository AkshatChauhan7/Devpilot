import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from "axios";
import { getSession, signOut } from "next-auth/react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/api/v1`,
      headers: {
        "Content-Type": "application/json",
      },
      timeout: 30000,
    });

    this.client.interceptors.request.use(
      async (config: InternalAxiosRequestConfig) => {
        const session = await getSession();
        if (session?.accessToken) {
          config.headers.Authorization = `Bearer ${session.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          if (typeof window !== "undefined") {
            await signOut({ callbackUrl: "/login" });
          }
        }
        return Promise.reject(error);
      }
    );
  }

  get instance() {
    return this.client;
  }

  // Auth
  async githubOAuthUrl() {
    const response = await this.client.get("/auth/github/url");
    return response.data;
  }

  async getMe() {
    const response = await this.client.get("/auth/me");
    return response.data;
  }

  // Users
  async getUsers(params?: { page?: number; page_size?: number }) {
    const response = await this.client.get("/users", { params });
    return response.data;
  }

  async getUser(userId: number) {
    const response = await this.client.get(`/users/${userId}`);
    return response.data;
  }

  // Repositories
  async getRepositories(params?: {
    page?: number;
    page_size?: number;
    search?: string;
    language?: string;
    installation_id?: number;
  }) {
    const response = await this.client.get("/repositories", { params });
    return response.data;
  }

  async getRepository(repoId: number) {
    const response = await this.client.get(`/repositories/${repoId}`);
    return response.data;
  }

  async createRepository(data: { github_id: number; installation_id?: number }) {
    const response = await this.client.post("/repositories", data);
    return response.data;
  }

  async syncRepositories(installationId: number) {
    const response = await this.client.post("/repositories/sync", { installation_id: installationId });
    return response.data;
  }

  async analyzeRepository(repoId: number) {
    const response = await this.client.post(`/repositories/${repoId}/analyze`);
    return response.data;
  }

  // Installations
  async getInstallations(params?: { page?: number; page_size?: number }) {
    const response = await this.client.get("/installations", { params });
    return response.data;
  }

  async getInstallation(installationId: number) {
    const response = await this.client.get(`/installations/${installationId}`);
    return response.data;
  }

  async getInstallationToken(installationId: number) {
    const response = await this.client.post(`/installations/${installationId}/token`);
    return response.data;
  }

  // Tasks
  async getTasks(params?: {
    page?: number;
    page_size?: number;
    status?: string;
    type?: string;
    repository_id?: number;
  }) {
    const response = await this.client.get("/tasks", { params });
    return response.data;
  }

  async getTask(taskId: number) {
    const response = await this.client.get(`/tasks/${taskId}`);
    return response.data;
  }

  async createTask(data: {
    type: string;
    title: string;
    description?: string;
    input_data?: Record<string, any>;
    repository_id?: number;
  }) {
    const response = await this.client.post("/tasks", data);
    return response.data;
  }

  async cancelTask(taskId: number) {
    const response = await this.client.post(`/tasks/${taskId}/cancel`);
    return response.data;
  }

  // Executions
  async getExecutions(params?: {
    page?: number;
    page_size?: number;
    status?: string;
    task_id?: number;
    repository_id?: number;
  }) {
    const response = await this.client.get("/executions", { params });
    return response.data;
  }

  async getExecution(executionId: number) {
    const response = await this.client.get(`/executions/${executionId}`);
    return response.data;
  }

  async createExecution(data: {
    command: string;
    working_directory?: string;
    image: string;
    environment?: Record<string, string>;
    timeout?: number;
    task_id?: number;
    repository_id?: number;
  }) {
    const response = await this.client.post("/executions", data);
    return response.data;
  }

  async cancelExecution(executionId: number) {
    const response = await this.client.post(`/executions/${executionId}/cancel`);
    return response.data;
  }

  async getExecutionLogs(executionId: number) {
    const response = await this.client.get(`/executions/${executionId}/logs`);
    return response.data;
  }

  // Pull Requests
  async getPullRequests(params?: {
    page?: number;
    page_size?: number;
    status?: string;
    repository_id?: number;
    task_id?: number;
  }) {
    const response = await this.client.get("/pull-requests", { params });
    return response.data;
  }

  async getPullRequest(prId: number) {
    const response = await this.client.get(`/pull-requests/${prId}`);
    return response.data;
  }

  async createPullRequest(data: {
    title: string;
    body?: string;
    head_branch: string;
    base_branch?: string;
    is_draft?: boolean;
    review_required?: boolean;
    repository_id: number;
    task_id?: number;
  }) {
    const response = await this.client.post("/pull-requests", data);
    return response.data;
  }

  async mergePullRequest(prId: number, mergeMethod?: string) {
    const response = await this.client.post(`/pull-requests/${prId}/merge`, {
      merge_method: mergeMethod || "merge",
    });
    return response.data;
  }

  async closePullRequest(prId: number) {
    const response = await this.client.post(`/pull-requests/${prId}/close`);
    return response.data;
  }

  // GitHub
  async getGitHubUser() {
    const response = await this.client.get("/github/user");
    return response.data;
  }

  async getGitHubRepositories(installationId?: number) {
    const response = await this.client.get("/github/repositories", {
      params: { installation_id: installationId },
    });
    return response.data;
  }

  async getGitHubRepository(owner: string, repo: string, installationId?: number) {
    const response = await this.client.get(`/github/repositories/${owner}/${repo}`, {
      params: { installation_id: installationId },
    });
    return response.data;
  }

  async getRepositoryContents(
    owner: string,
    repo: string,
    path?: string,
    ref?: string,
    installationId?: number
  ) {
    const response = await this.client.get(`/github/repositories/${owner}/${repo}/contents`, {
      params: { path, ref, installation_id: installationId },
    });
    return response.data;
  }

  async listBranches(owner: string, repo: string, installationId?: number) {
    const response = await this.client.get(`/github/repositories/${owner}/${repo}/branches`, {
      params: { installation_id: installationId },
    });
    return response.data;
  }

  async listCommits(
    owner: string,
    repo: string,
    params?: { sha?: string; path?: string; per_page?: number },
    installationId?: number
  ) {
    const response = await this.client.get(`/github/repositories/${owner}/${repo}/commits`, {
      params: { ...params, installation_id: installationId },
    });
    return response.data;
  }

  async createBranch(
    owner: string,
    repo: string,
    branchName: string,
    fromBranch: string,
    installationId?: number
  ) {
    const response = await this.client.post(
      `/github/repositories/${owner}/${repo}/create-branch`,
      { branch_name: branchName, from_branch: fromBranch },
      { params: { installation_id: installationId } }
    );
    return response.data;
  }

  async createFile(
    owner: string,
    repo: string,
    path: string,
    content: string,
    message: string,
    branch: string,
    installationId?: number
  ) {
    const response = await this.client.post(
      `/github/repositories/${owner}/${repo}/create-file`,
      { path, content, message, branch },
      { params: { installation_id: installationId } }
    );
    return response.data;
  }

  async updateFile(
    owner: string,
    repo: string,
    path: string,
    content: string,
    message: string,
    branch: string,
    sha: string,
    installationId?: number
  ) {
    const response = await this.client.post(
      `/github/repositories/${owner}/${repo}/update-file`,
      { path, content, message, branch, sha },
      { params: { installation_id: installationId } }
    );
    return response.data;
  }

  async deleteFile(
    owner: string,
    repo: string,
    path: string,
    message: string,
    branch: string,
    sha: string,
    installationId?: number
  ) {
    const response = await this.client.delete(
      `/github/repositories/${owner}/${repo}/delete-file`,
      { data: { path, message, branch, sha }, params: { installation_id: installationId } }
    );
    return response.data;
  }
}

export const api = new ApiClient();