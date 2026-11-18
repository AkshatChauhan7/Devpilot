"""Schemas package initialization."""
from app.schemas.user import UserRead, UserCreate, UserUpdate
from app.schemas.repository import RepositoryRead, RepositoryCreate, RepositoryUpdate, RepositoryList
from app.schemas.installation import InstallationRead, InstallationCreate
from app.schemas.task import TaskRead, TaskCreate, TaskUpdate, TaskList, TaskStatus, TaskType
from app.schemas.execution import ExecutionRead, ExecutionCreate, ExecutionStatus
from app.schemas.pull_request import PullRequestRead, PullRequestCreate, PullRequestUpdate, PRStatus
from app.schemas.github import GitHubWebhookEvent, GitHubAppAuth, GitHubOAuthCallback
from app.schemas.common import PaginatedResponse, ErrorResponse, SuccessResponse

__all__ = [
    "UserRead",
    "UserCreate",
    "UserUpdate",
    "RepositoryRead",
    "RepositoryCreate",
    "RepositoryUpdate",
    "RepositoryList",
    "InstallationRead",
    "InstallationCreate",
    "TaskRead",
    "TaskCreate",
    "TaskUpdate",
    "TaskList",
    "TaskStatus",
    "TaskType",
    "ExecutionRead",
    "ExecutionCreate",
    "ExecutionStatus",
    "PullRequestRead",
    "PullRequestCreate",
    "PullRequestUpdate",
    "PRStatus",
    "GitHubWebhookEvent",
    "GitHubAppAuth",
    "GitHubOAuthCallback",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
]