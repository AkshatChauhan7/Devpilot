"""GitHub API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.repository import Repository
from app.models.installation import Installation
from app.services.github import GitHubService

router = APIRouter()


@router.get("/user")
async def get_github_user(
    current_user: User = Depends(get_current_user),
):
    """Get authenticated GitHub user info."""
    if not current_user.access_token:
        raise HTTPException(status_code=401, detail="No GitHub access token")

    github_service = GitHubService()
    user_info = await github_service.get_user_info(current_user.access_token)
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user info")

    return user_info


@router.get("/repositories")
async def list_github_repositories(
    installation_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
):
    """List repositories from GitHub."""
    github_service = GitHubService()

    if installation_id:
        # Use installation token
        token = await github_service.get_installation_token(installation_id)
        if not token:
            raise HTTPException(status_code=404, detail="Installation not found")
    elif current_user.access_token:
        # Use user OAuth token
        token = current_user.access_token
    else:
        raise HTTPException(status_code=401, detail="No authentication available")

    repos = await github_service.get_user_repositories(token)
    return repos


@router.get("/repositories/{owner}/{repo}")
async def get_github_repository(
    owner: str,
    repo: str,
    installation_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
):
    """Get repository details from GitHub."""
    github_service = GitHubService()

    if installation_id:
        token = await github_service.get_installation_token(installation_id)
    elif current_user.access_token:
        token = current_user.access_token
    else:
        raise HTTPException(status_code=401, detail="No authentication available")

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    repo_data = await github_service.get_repository(token, owner, repo)
    if not repo_data:
        raise HTTPException(status_code=404, detail="Repository not found")

    return repo_data


@router.get("/repositories/{owner}/{repo}/contents")
async def get_repository_contents(
    owner: str,
    repo: str,
    path: str = Query(""),
    ref: str | None = Query(None),
    installation_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
):
    """Get repository contents from GitHub."""
    github_service = GitHubService()

    if installation_id:
        token = await github_service.get_installation_token(installation_id)
    elif current_user.access_token:
        token = current_user.access_token
    else:
        raise HTTPException(status_code=401, detail="No authentication available")

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    contents = await github_service.get_contents(token, owner, repo, path, ref)
    return contents


@router.get("/repositories/{owner}/{repo}/branches")
async def list_branches(
    owner: str,
    repo: str,
    installation_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
):
    """List repository branches."""
    github_service = GitHubService()

    if installation_id:
        token = await github_service.get_installation_token(installation_id)
    elif current_user.access_token:
        token = current_user.access_token
    else:
        raise HTTPException(status_code=401, detail="No authentication available")

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    branches = await github_service.get_branches(token, owner, repo)
    return branches


@router.get("/repositories/{owner}/{repo}/commits")
async def list_commits(
    owner: str,
    repo: str,
    sha: str | None = Query(None),
    path: str | None = Query(None),
    since: str | None = Query(None),
    until: str | None = Query(None),
    per_page: int = Query(30, ge=1, le=100),
    installation_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
):
    """List repository commits."""
    github_service = GitHubService()

    if installation_id:
        token = await github_service.get_installation_token(installation_id)
    elif current_user.access_token:
        token = current_user.access_token
    else:
        raise HTTPException(status_code=401, detail="No authentication available")

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    commits = await github_service.get_commits(
        token, owner, repo, sha=sha, path=path, since=since, until=until, per_page=per_page
    )
    return commits


@router.post("/repositories/{owner}/{repo}/create-branch")
async def create_branch(
    owner: str,
    repo: str,
    branch_name: str,
    from_branch: str = "main",
    installation_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
):
    """Create a new branch."""
    github_service = GitHubService()

    if installation_id:
        token = await github_service.get_installation_token(installation_id)
    elif current_user.access_token:
        token = current_user.access_token
    else:
        raise HTTPException(status_code=401, detail="No authentication available")

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    result = await github_service.create_branch(token, owner, repo, branch_name, from_branch)
    return result


@router.post("/repositories/{owner}/{repo}/create-file")
async def create_file(
    owner: str,
    repo: str,
    path: str,
    content: str,
    message: str,
    branch: str,
    installation_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
):
    """Create a file in repository."""
    github_service = GitHubService()

    if installation_id:
        token = await github_service.get_installation_token(installation_id)
    elif current_user.access_token:
        token = current_user.access_token
    else:
        raise HTTPException(status_code=401, detail="No authentication available")

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    result = await github_service.create_file(token, owner, repo, path, content, message, branch)
    return result


@router.post("/repositories/{owner}/{repo}/update-file")
async def update_file(
    owner: str,
    repo: str,
    path: str,
    content: str,
    message: str,
    branch: str,
    sha: str,
    installation_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
):
    """Update a file in repository."""
    github_service = GitHubService()

    if installation_id:
        token = await github_service.get_installation_token(installation_id)
    elif current_user.access_token:
        token = current_user.access_token
    else:
        raise HTTPException(status_code=401, detail="No authentication available")

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    result = await github_service.update_file(token, owner, repo, path, content, message, branch, sha)
    return result


@router.delete("/repositories/{owner}/{repo}/delete-file")
async def delete_file(
    owner: str,
    repo: str,
    path: str,
    message: str,
    branch: str,
    sha: str,
    installation_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
):
    """Delete a file in repository."""
    github_service = GitHubService()

    if installation_id:
        token = await github_service.get_installation_token(installation_id)
    elif current_user.access_token:
        token = current_user.access_token
    else:
        raise HTTPException(status_code=401, detail="No authentication available")

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    result = await github_service.delete_file(token, owner, repo, path, message, branch, sha)
    return result