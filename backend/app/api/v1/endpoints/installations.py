"""Installation endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_github_jwt
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.installation import Installation
from app.schemas.installation import InstallationRead, InstallationCreate
from app.schemas.common import PaginatedResponse
from app.services.github import GitHubService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[InstallationRead])
async def list_installations(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List GitHub App installations for the current user."""
    query = select(Installation).where(Installation.user_id == current_user.id)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Installation.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .options(selectinload(Installation.repositories))
    )
    installations = result.scalars().all()

    return PaginatedResponse.create(
        items=[InstallationRead.model_validate(i) for i in installations],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=InstallationRead, status_code=201)
async def create_installation(
    installation_create: InstallationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or update installation (from webhook)."""
    # Check if installation already exists
    result = await db.execute(
        select(Installation).where(Installation.github_id == installation_create.github_id)
    )
    installation = result.scalar_one_or_none()

    if installation:
        # Update existing
        update_data = installation_create.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(installation, field, value)
        installation.user_id = current_user.id
    else:
        # Create new
        installation = Installation(
            **installation_create.model_dump(),
            user_id=current_user.id,
        )
        db.add(installation)

    await db.commit()
    await db.refresh(installation)

    return InstallationRead.model_validate(installation)


@router.get("/{installation_id}", response_model=InstallationRead)
async def get_installation(
    installation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get installation by ID."""
    result = await db.execute(
        select(Installation)
        .where(Installation.id == installation_id, Installation.user_id == current_user.id)
        .options(selectinload(Installation.repositories))
    )
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    return InstallationRead.model_validate(installation)


@router.delete("/{installation_id}")
async def delete_installation(
    installation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete installation."""
    result = await db.execute(
        select(Installation).where(Installation.id == installation_id, Installation.user_id == current_user.id)
    )
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    await db.delete(installation)
    await db.commit()

    return {"message": "Installation deleted successfully"}


@router.get("/{installation_id}/token")
async def get_installation_token(
    installation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get GitHub App installation token."""
    result = await db.execute(
        select(Installation).where(Installation.id == installation_id, Installation.user_id == current_user.id)
    )
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    github_service = GitHubService()
    token = await github_service.get_installation_token(installation.github_id)
    if not token:
        raise HTTPException(status_code=500, detail="Failed to generate installation token")

    return {"token": token, "expires_at": "TODO"}


@router.post("/webhook")
async def github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub App webhooks."""
    payload = await request.json()
    headers = dict(request.headers)

    # Verify webhook signature
    if settings.GITHUB_WEBHOOK_SECRET:
        github_service = GitHubService()
        if not github_service.verify_webhook_signature(payload, headers):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event_type = headers.get("X-GitHub-Event", "unknown")
    action = payload.get("action")

    # Handle installation events
    if event_type == "installation":
        installation_data = payload.get("installation", {})
        if action in ["created", "new_permissions_accepted"]:
            # Create or update installation
            await _handle_installation_created(db, installation_data)
        elif action == "deleted":
            await _handle_installation_deleted(db, installation_data)

    # Handle repository events
    elif event_type == "repository":
        repo_data = payload.get("repository", {})
        installation_data = payload.get("installation", {})
        if action in ["created", "publicized"]:
            await _handle_repository_added(db, repo_data, installation_data)
        elif action in ["deleted", "privatized"]:
            await _handle_repository_removed(db, repo_data, installation_data)

    return {"status": "ok"}


async def _handle_installation_created(db: AsyncSession, installation_data: dict):
    """Handle installation created event."""
    github_id = installation_data["id"]
    account = installation_data["account"]

    result = await db.execute(select(Installation).where(Installation.github_id == github_id))
    installation = result.scalar_one_or_none()

    if installation:
        installation.permissions = str(installation_data.get("permissions", {}))
        installation.events = str(installation_data.get("events", []))
        installation.repository_selection = installation_data.get("repository_selection", "all")
        installation.suspended_at = None
    else:
        installation = Installation(
            github_id=github_id,
            account_login=account["login"],
            account_type=account["type"],
            account_id=account["id"],
            account_avatar_url=account.get("avatar_url"),
            account_html_url=account["html_url"],
            target_type=installation_data.get("target_type", "Organization"),
            permissions=str(installation_data.get("permissions", {})),
            events=str(installation_data.get("events", [])),
            repository_selection=installation_data.get("repository_selection", "all"),
        )
        db.add(installation)

    await db.commit()


async def _handle_installation_deleted(db: AsyncSession, installation_data: dict):
    """Handle installation deleted event."""
    github_id = installation_data["id"]
    result = await db.execute(select(Installation).where(Installation.github_id == github_id))
    installation = result.scalar_one_or_none()

    if installation:
        installation.suspended_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        await db.commit()


async def _handle_repository_added(db: AsyncSession, repo_data: dict, installation_data: dict):
    """Handle repository added to installation."""
    # This would sync the repository - implementation depends on user mapping
    pass


async def _handle_repository_removed(db: AsyncSession, repo_data: dict, installation_data: dict):
    """Handle repository removed from installation."""
    github_id = repo_data["id"]
    result = await db.execute(select(Repository).where(Repository.github_id == github_id))
    repository = result.scalar_one_or_none()

    if repository:
        repository.installation_id = None
        await db.commit()