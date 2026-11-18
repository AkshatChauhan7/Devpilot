"""API v1 router."""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    repositories,
    installations,
    tasks,
    executions,
    pull_requests,
    github,
    websocket,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(repositories.router, prefix="/repositories", tags=["Repositories"])
api_router.include_router(installations.router, prefix="/installations", tags=["Installations"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(executions.router, prefix="/executions", tags=["Executions"])
api_router.include_router(pull_requests.router, prefix="/pull-requests", tags=["Pull Requests"])
api_router.include_router(github.router, prefix="/github", tags=["GitHub"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])