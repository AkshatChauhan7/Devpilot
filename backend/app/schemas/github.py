"""GitHub-related schemas."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, HttpUrl


class GitHubAppAuth(BaseModel):
    """GitHub App authentication response."""
    token: str
    expires_at: str
    repositories: List[Dict[str, Any]]


class GitHubOAuthCallback(BaseModel):
    """GitHub OAuth callback parameters."""
    code: str
    state: Optional[str] = None


class GitHubWebhookEvent(BaseModel):
    """Base GitHub webhook event."""
    action: Optional[str] = None
    installation: Optional[Dict[str, Any]] = None
    repository: Optional[Dict[str, Any]] = None
    sender: Optional[Dict[str, Any]] = None


class InstallationEvent(GitHubWebhookEvent):
    """Installation webhook event."""
    action: str  # created, deleted, suspend, unsuspend, new_permissions_accepted
    repositories_added: Optional[List[Dict[str, Any]]] = None
    repositories_removed: Optional[List[Dict[str, Any]]] = None


class RepositoryEvent(GitHubWebhookEvent):
    """Repository webhook event."""
    action: str  # created, deleted, archived, unarchived, edited, renamed, transferred, publicized, privatized


class PushEvent(GitHubWebhookEvent):
    """Push webhook event."""
    ref: str
    before: str
    after: str
    commits: List[Dict[str, Any]]
    pusher: Dict[str, Any]


class PullRequestEvent(GitHubWebhookEvent):
    """Pull request webhook event."""
    action: str  # opened, closed, reopened, synchronize, edited, labeled, unlabeled, review_requested
    number: int
    pull_request: Dict[str, Any]


class IssueEvent(GitHubWebhookEvent):
    """Issue webhook event."""
    action: str  # opened, closed, reopened, edited, labeled, unlabeled, assigned, unassigned
    issue: Dict[str, Any]


class WorkflowRunEvent(GitHubWebhookEvent):
    """Workflow run webhook event."""
    action: str  # requested, in_progress, completed
    workflow_run: Dict[str, Any]