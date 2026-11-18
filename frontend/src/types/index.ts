export interface User {
  id: number;
  github_id: number;
  username: string;
  email?: string;
  name?: string;
  avatar_url?: string;
  role: string;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}

export interface Repository {
  id: number;
  github_id: number;
  name: string;
  full_name: string;
  description?: string;
  html_url: string;
  clone_url: string;
  ssh_url: string;
  default_branch: string;
  language?: string;
  stars: number;
  forks: number;
  is_private: boolean;
  is_fork: boolean;
  is_archived: boolean;
  owner_id: number;
  installation_id?: number;
  created_at: string;
  updated_at: string;
  last_analyzed_at?: string;
  analysis_status: string;
  analysis_error?: string;
}

export interface Installation {
  id: number;
  github_id: number;
  account_login: string;
  account_type: string;
  account_id: number;
  account_avatar_url?: string;
  account_html_url: string;
  target_type: string;
  permissions: Record<string, any>;
  events: string[];
  repository_selection: string;
  created_at: string;
  updated_at: string;
  suspended_at?: string;
  user_id?: number;
}

export type TaskStatus = "pending" | "queued" | "running" | "completed" | "failed" | "cancelled";
export type TaskType =
  | "repository_analysis"
  | "bug_detection"
  | "code_generation"
  | "code_modification"
  | "test_generation"
  | "test_execution"
  | "pr_creation"
  | "dependency_update"
  | "security_scan";

export interface Task {
  id: number;
  task_id: string;
  type: TaskType;
  status: TaskStatus;
  title: string;
  description?: string;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  progress: number;
  current_step?: string;
  total_steps: number;
  user_id: number;
  repository_id?: number;
  parent_task_id?: number;
  celery_task_id?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  repository?: Repository;
  subtasks?: Task[];
  executions?: Execution[];
}

export type ExecutionStatus =
  | "pending"
  | "queued"
  | "preparing"
  | "running"
  | "completed"
  | "failed"
  | "timeout"
  | "cancelled";

export interface Execution {
  id: number;
  execution_id: string;
  status: ExecutionStatus;
  command: string;
  working_directory: string;
  image: string;
  environment?: Record<string, string>;
  timeout: number;
  cpu_limit?: number;
  memory_limit?: string;
  stdout?: string;
  stderr?: string;
  exit_code?: number;
  duration_ms?: number;
  error_message?: string;
  task_id?: number;
  repository_id?: number;
  container_id?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export type PRStatus = "draft" | "open" | "closed" | "merged" | "failed";

export interface PullRequest {
  id: number;
  github_pr_id?: number;
  github_pr_number?: number;
  title: string;
  body?: string;
  head_branch: string;
  base_branch: string;
  status: PRStatus;
  is_draft: boolean;
  mergeable?: boolean;
  merge_commit_sha?: string;
  head_sha?: string;
  base_sha?: string;
  changes_summary?: string;
  files_changed?: number;
  additions?: number;
  deletions?: number;
  review_required: boolean;
  approved_by?: string;
  merged_at?: string;
  closed_at?: string;
  task_id?: number;
  repository_id: number;
  created_at: string;
  updated_at: string;
  repository?: Repository;
  task?: Task;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface GitHubRepository {
  id: number;
  name: string;
  full_name: string;
  description?: string;
  html_url: string;
  clone_url: string;
  ssh_url: string;
  default_branch: string;
  language?: string;
  stargazers_count: number;
  forks_count: number;
  private: boolean;
  fork: boolean;
  archived: boolean;
}

export interface GitHubFile {
  name: string;
  path: string;
  sha: string;
  size: number;
  url: string;
  html_url: string;
  git_url: string;
  download_url: string;
  type: "file" | "dir" | "symlink" | "submodule";
  content?: string;
  encoding?: string;
}

export interface GitHubBranch {
  name: string;
  commit: {
    sha: string;
    url: string;
  };
  protected: boolean;
}

export interface GitHubCommit {
  sha: string;
  commit: {
    author: {
      name: string;
      email: string;
      date: string;
    };
    committer: {
      name: string;
      email: string;
      date: string;
    };
    message: string;
    tree: {
      sha: string;
      url: string;
    };
    url: string;
    comment_count: number;
    verification: {
      verified: boolean;
      reason: string;
      signature: string;
      payload: string;
    };
  };
  url: string;
  html_url: string;
  comments_url: string;
  author?: {
    login: string;
    id: number;
    avatar_url: string;
    url: string;
  };
  committer?: {
    login: string;
    id: number;
    avatar_url: string;
    url: string;
  };
  parents: Array<{
    sha: string;
    url: string;
    html_url: string;
  }>;
}

export interface WebSocketMessage {
  type: "task_update" | "execution_update" | "task_state" | "execution_state" | "pong";
  task_id?: number;
  execution_id?: number;
  status?: string;
  progress?: number;
  current_step?: string;
  stdout?: string;
  stderr?: string;
  exit_code?: number;
}