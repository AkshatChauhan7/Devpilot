"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
    create_github_jwt,
)
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserWithToken
from app.services.github import GitHubService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user."""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Get current user if authenticated, otherwise None."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    result = await db.execute(select(User).where(User.id == int(user_id)))
    return result.scalar_one_or_none()


@router.post("/github/callback", response_model=UserWithToken)
async def github_oauth_callback(
    code: str,
    state: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub OAuth callback."""
    github_service = GitHubService()

    # Exchange code for access token
    token_data = await github_service.exchange_code_for_token(code)
    if not token_data:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")

    access_token = token_data["access_token"]

    # Get user info from GitHub
    user_info = await github_service.get_user_info(access_token)
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user info")

    # Check if user exists
    result = await db.execute(select(User).where(User.github_id == user_info["id"]))
    user = result.scalar_one_or_none()

    if user:
        # Update existing user
        user.username = user_info["login"]
        user.email = user_info.get("email")
        user.name = user_info.get("name")
        user.avatar_url = user_info.get("avatar_url")
        user.access_token = access_token  # In production, encrypt this
        user.last_login_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    else:
        # Create new user
        user = User(
            github_id=user_info["id"],
            username=user_info["login"],
            email=user_info.get("email"),
            name=user_info.get("name"),
            avatar_url=user_info.get("avatar_url"),
            access_token=access_token,
            last_login_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    # Create JWT token
    jwt_token = create_access_token({"sub": str(user.id), "github_id": user.github_id})

    return UserWithToken(
        **UserRead.model_validate(user).model_dump(),
        access_token=jwt_token,
    )


@router.get("/github/url")
async def github_oauth_url():
    """Get GitHub OAuth authorization URL."""
    if not settings.GITHUB_OAUTH_CLIENT_ID:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured")

    github_service = GitHubService()
    url, state = github_service.get_oauth_url()
    return {"url": url, "state": state}


@router.post("/token", response_model=UserWithToken)
async def login(
    username: str,
    password: str,
    db: AsyncSession = Depends(get_db),
):
    """Login with username and password (for testing)."""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.access_token or ""):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    jwt_token = create_access_token({"sub": str(user.id), "github_id": user.github_id})

    return UserWithToken(
        **UserRead.model_validate(user).model_dump(),
        access_token=jwt_token,
    )


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return UserRead.model_validate(current_user)


@router.post("/refresh", response_model=UserWithToken)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token."""
    jwt_token = create_access_token({"sub": str(current_user.id), "github_id": current_user.github_id})

    return UserWithToken(
        **UserRead.model_validate(current_user).model_dump(),
        access_token=jwt_token,
    )


@router.post("/github/app-token")
async def get_github_app_token(installation_id: int, db: AsyncSession = Depends(get_db)):
    """Get GitHub App installation token."""
    if not settings.GITHUB_APP_ID or not settings.GITHUB_APP_PRIVATE_KEY:
        raise HTTPException(status_code=503, detail="GitHub App not configured")

    github_service = GitHubService()
    token = await github_service.get_installation_token(installation_id)
    if not token:
        raise HTTPException(status_code=404, detail="Installation not found or token generation failed")

    return {"token": token}