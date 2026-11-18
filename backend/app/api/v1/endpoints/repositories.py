"""Repository endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.repository import Repository
from app.schemas.repository import RepositoryRead, RepositoryCreate, RepositoryUpdate, RepositoryList
from app.schemas.common import PaginatedResponse
from app.services.github import GitHubService
from app.tasks.repository import analyze_repository_task

router = APIRouter()


@router.get("", response_model=PaginatedResponse[RepositoryRead])
async def list_repositories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    language: str | None = Query(None),
    installation_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List repositories accessible to the current user."""
    query = select(Repository).where(Repository.owner_id == current_user.id)

    if installation_id:
        query = query.where(Repository.installation_id == installation_id)

    if search:
        query = query.where(
            or_(
                Repository.name.ilike(f"%{search}%"),
                Repository.full_name.ilike(f"%{search}%"),
                Repository.description.ilike(f"%{search}%"),
            )
        )

    if language:
        query = query.where(Repository.language == language)

    # Get total count
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    # Get paginated repositories
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Repository.updated_at.desc())
        .offset(offset)
        .limit(page_size)
        .options(selectinload(Repository.installation))
    )
    repositories = result.scalars().all()

    return PaginatedResponse.create(
        items=[RepositoryRead.model_validate(r) for r in repositories],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=RepositoryRead, status_code=201)
async def create_repository(
    repo_create: RepositoryCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a repository (sync from GitHub)."""
    # Check if repository already exists
    result = await db.execute(
        select(Repository).where(
            Repository.github_id == repo_create.github_id,
            Repository.owner_id == current_user.id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Repository already exists")

    # Create repository record
    repository = Repository(
        **repo_create.model_dump(),
        owner_id=current_user.id,
    )
    db.add(repository)
    await db.commit()
    await db.refresh(repository)

    # Trigger analysis in background
    background_tasks.add_task(analyze_repository_task, repository.id)

    return RepositoryRead.model_validate(repository)


@router.post("/sync", response_model=list[RepositoryRead])
async def sync_repositories(
    installation_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync repositories from a GitHub installation."""
    github_service = GitHubService()
    token = await github_service.get_installation_token(installation_id)
    if not token:
        raise HTTPException(status_code=404, detail="Installation not found")

    repos = await github_service.get_installation_repositories(token)
    if not repos:
        return []

    created_repos = []
    for repo_data in repos:
        # Check if already exists
        result = await db.execute(
            select(Repository).where(
                Repository.github_id == repo_data["id"],
                Repository.owner_id == current_user.id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.name = repo_data["name"]
            existing.full_name = repo_data["full_name"]
            existing.description = repo_data.get("description")
            existing.html_url = repo_data["html_url"]
            existing.clone_url = repo_data["clone_url"]
            existing.ssh_url = repo_data["ssh_url"]
            existing.default_branch = repo_data["default_branch"]
            existing.language = repo_data.get("language")
            existing.stars = repo_data["stargazers_count"]
            existing.forks = repo_data["forks_count"]
            existing.is_private = repo_data["private"]
            existing.is_fork = repo_data["fork"]
            existing.is_archived = repo_data["archived"]
            existing.installation_id = installation_id
            await db.commit()
            await db.refresh(existing)
            created_repos.append(existing)
        else:
            # Create new
            repository = Repository(
                github_id=repo_data["id"],
                name=repo_data["name"],
                full_name=repo_data["full_name"],
                description=repo_data.get("description"),
                html_url=repo_data["html_url"],
                clone_url=repo_data["clone_url"],
                ssh_url=repo_data["ssh_url"],
                default_branch=repo_data["default_branch"],
                language=repo_data.get("language"),
                stars=repo_data["stargazers_count"],
                forks=repo_data["forks_count"],
                is_private=repo_data["private"],
                is_fork=repo_data["fork"],
                is_archived=repo_data["archived"],
                owner_id=current_user.id,
                installation_id=installation_id,
            )
            db.add(repository)
            await db.commit()
            await db.refresh(repository)
            created_repos.append(repository)

        # Trigger analysis
        background_tasks.add_task(analyze_repository_task, created_repos[-1].id)

    return [RepositoryRead.model_validate(r) for r in created_repos]


@router.get("/{repo_id}", response_model=RepositoryRead)
async def get_repository(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get repository by ID."""
    result = await db.execute(
        select(Repository)
        .where(Repository.id == repo_id, Repository.owner_id == current_user.id)
        .options(selectinload(Repository.installation))
    )
    repository = result.scalar_one_or_none()

    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    return RepositoryRead.model_validate(repository)


@router.patch("/{repo_id}", response_model=RepositoryRead)
async def update_repository(
    repo_id: int,
    repo_update: RepositoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update repository."""
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.owner_id == current_user.id)
    )
    repository = result.scalar_one_or_none()

    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    update_data = repo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(repository, field, value)

    await db.commit()
    await db.refresh(repository)

    return RepositoryRead.model_validate(repository)


@router.delete("/{repo_id}")
async def delete_repository(
    repo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete repository."""
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.owner_id == current_user.id)
    )
    repository = result.scalar_one_or_none()

    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    await db.delete(repository)
    await db.commit()

    return {"message": "Repository deleted successfully"}


@router.post("/{repo_id}/analyze")
async def analyze_repository(
    repo_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger repository analysis."""
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.owner_id == current_user.id)
    )
    repository = result.scalar_one_or_none()

    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    background_tasks.add_task(analyze_repository_task, repo_id)

    return {"message": "Analysis started", "repository_id": repo_id}