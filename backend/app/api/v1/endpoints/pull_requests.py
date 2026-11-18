"""Pull Request endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.pull_request import PullRequest, PRStatus
from app.models.repository import Repository
from app.schemas.pull_request import PullRequestRead, PullRequestCreate, PullRequestUpdate, PRStatus as PRStatusEnum
from app.schemas.common import PaginatedResponse
from app.services.github import GitHubService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[PullRequestRead])
async def list_pull_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: PRStatusEnum | None = Query(None),
    repository_id: int | None = Query(None),
    task_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List pull requests for the current user."""
    query = select(PullRequest).join(Repository).where(Repository.owner_id == current_user.id)

    if status:
        query = query.where(PullRequest.status == status)

    if repository_id:
        query = query.where(PullRequest.repository_id == repository_id)

    if task_id:
        query = query.where(PullRequest.task_id == task_id)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(PullRequest.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .options(selectinload(PullRequest.repository), selectinload(PullRequest.task))
    )
    prs = result.scalars().all()

    return PaginatedResponse.create(
        items=[PullRequestRead.model_validate(pr) for pr in prs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=PullRequestRead, status_code=201)
async def create_pull_request(
    pr_create: PullRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new pull request."""
    # Verify repository access
    result = await db.execute(
        select(Repository).where(
            Repository.id == pr_create.repository_id,
            Repository.owner_id == current_user.id,
        )
    )
    repository = result.scalar_one_or_none()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Verify task access if provided
    if pr_create.task_id:
        from app.models.task import Task
        result = await db.execute(
            select(Task).where(Task.id == pr_create.task_id, Task.user_id == current_user.id)
        )
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

    # Create PR record
    pr = PullRequest(
        title=pr_create.title,
        body=pr_create.body,
        head_branch=pr_create.head_branch,
        base_branch=pr_create.base_branch,
        is_draft=pr_create.is_draft,
        review_required=pr_create.review_required,
        task_id=pr_create.task_id,
        repository_id=pr_create.repository_id,
        status=PRStatus.DRAFT,
    )
    db.add(pr)
    await db.commit()
    await db.refresh(pr)

    # Create PR on GitHub
    github_service = GitHubService()
    if repository.installation_id:
        install_result = await db.execute(
            select(Installation).where(Installation.id == repository.installation_id)
        )
        installation = install_result.scalar_one_or_none()
        if installation:
            token = await github_service.get_installation_token(installation.github_id)
            if token:
                github_pr = await github_service.create_pull_request(
                    token=token,
                    owner=repository.full_name.split("/")[0],
                    repo=repository.full_name.split("/")[1],
                    title=pr.title,
                    body=pr.body or "",
                    head=pr.head_branch,
                    base=pr.base_branch,
                    draft=pr.is_draft,
                )
                if github_pr:
                    pr.github_pr_id = github_pr["id"]
                    pr.github_pr_number = github_pr["number"]
                    pr.head_sha = github_pr["head"]["sha"]
                    pr.base_sha = github_pr["base"]["sha"]
                    pr.status = PRStatus.OPEN if not pr.is_draft else PRStatus.DRAFT
                    await db.commit()
                    await db.refresh(pr)

    return PullRequestRead.model_validate(pr)


@router.get("/{pr_id}", response_model=PullRequestRead)
async def get_pull_request(
    pr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pull request by ID."""
    result = await db.execute(
        select(PullRequest)
        .join(Repository)
        .where(PullRequest.id == pr_id, Repository.owner_id == current_user.id)
        .options(selectinload(PullRequest.repository), selectinload(PullRequest.task))
    )
    pr = result.scalar_one_or_none()

    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    return PullRequestRead.model_validate(pr)


@router.patch("/{pr_id}", response_model=PullRequestRead)
async def update_pull_request(
    pr_id: int,
    pr_update: PullRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update pull request."""
    result = await db.execute(
        select(PullRequest)
        .join(Repository)
        .where(PullRequest.id == pr_id, Repository.owner_id == current_user.id)
    )
    pr = result.scalar_one_or_none()

    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    update_data = pr_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pr, field, value)

    # Sync with GitHub if status changed
    if "status" in update_data and pr.github_pr_id and pr.repository.installation_id:
        github_service = GitHubService()
        install_result = await db.execute(
            select(Installation).where(Installation.id == pr.repository.installation_id)
        )
        installation = install_result.scalar_one_or_none()
        if installation:
            token = await github_service.get_installation_token(installation.github_id)
            if token:
                # Update PR on GitHub
                pass

    await db.commit()
    await db.refresh(pr)

    return PullRequestRead.model_validate(pr)


@router.post("/{pr_id}/merge")
async def merge_pull_request(
    pr_id: int,
    merge_method: str = Query("merge", pattern="^(merge|squash|rebase)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Merge pull request."""
    result = await db.execute(
        select(PullRequest)
        .join(Repository)
        .where(PullRequest.id == pr_id, Repository.owner_id == current_user.id)
    )
    pr = result.scalar_one_or_none()

    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    if pr.status not in [PRStatus.OPEN, PRStatus.DRAFT]:
        raise HTTPException(status_code=400, detail="Pull request cannot be merged")

    if not pr.github_pr_id or not pr.repository.installation_id:
        raise HTTPException(status_code=400, detail="Pull request not linked to GitHub")

    github_service = GitHubService()
    install_result = await db.execute(
        select(Installation).where(Installation.id == pr.repository.installation_id)
    )
    installation = install_result.scalar_one_or_none()
    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    token = await github_service.get_installation_token(installation.github_id)
    if not token:
        raise HTTPException(status_code=500, detail="Failed to get installation token")

    merged = await github_service.merge_pull_request(
        token=token,
        owner=pr.repository.full_name.split("/")[0],
        repo=pr.repository.full_name.split("/")[1],
        pr_number=pr.github_pr_number,
        merge_method=merge_method,
    )

    if merged:
        pr.status = PRStatus.MERGED
        pr.merged_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        pr.merge_commit_sha = merged.get("sha")
        await db.commit()
        return {"message": "Pull request merged successfully", "commit_sha": merged.get("sha")}

    raise HTTPException(status_code=400, detail="Failed to merge pull request")


@router.post("/{pr_id}/close")
async def close_pull_request(
    pr_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Close pull request."""
    result = await db.execute(
        select(PullRequest)
        .join(Repository)
        .where(PullRequest.id == pr_id, Repository.owner_id == current_user.id)
    )
    pr = result.scalar_one_or_none()

    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    if pr.status == PRStatus.CLOSED:
        return {"message": "Pull request already closed"}

    if pr.github_pr_id and pr.repository.installation_id:
        github_service = GitHubService()
        install_result = await db.execute(
            select(Installation).where(Installation.id == pr.repository.installation_id)
        )
        installation = install_result.scalar_one_or_none()
        if installation:
            token = await github_service.get_installation_token(installation.github_id)
            if token:
                await github_service.close_pull_request(
                    token=token,
                    owner=pr.repository.full_name.split("/")[0],
                    repo=pr.repository.full_name.split("/")[1],
                    pr_number=pr.github_pr_number,
                )

    pr.status = PRStatus.CLOSED
    pr.closed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    await db.commit()

    return {"message": "Pull request closed successfully"}