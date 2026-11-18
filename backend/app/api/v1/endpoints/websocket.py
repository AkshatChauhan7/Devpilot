"""WebSocket endpoints for real-time updates."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Set
import json
import asyncio

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.task import Task

router = APIRouter()

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Connection might be closed
                    pass

    async def broadcast(self, message: dict):
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


async def get_user_from_token(token: str, db: AsyncSession) -> User | None:
    """Get user from JWT token."""
    payload = decode_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    result = await db.execute(select(User).where(User.id == int(user_id)))
    return result.scalar_one_or_none()


@router.websocket("/tasks/{task_id}")
async def websocket_task_updates(
    websocket: WebSocket,
    task_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for real-time task updates."""
    user = await get_user_from_token(token, db)
    if not user:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Verify task ownership
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        await websocket.close(code=4004, reason="Task not found")
        return

    await manager.connect(websocket, user.id)

    try:
        # Send initial task state
        await websocket.send_json({
            "type": "task_state",
            "task_id": task.id,
            "status": task.status.value,
            "progress": task.progress,
            "current_step": task.current_step,
        })

        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("type") == "subscribe":
                # Subscribe to specific events
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id)
    except Exception as e:
        manager.disconnect(websocket, user.id)
        await websocket.close(code=4000, reason=str(e))


@router.websocket("/executions/{execution_id}")
async def websocket_execution_updates(
    websocket: WebSocket,
    execution_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for real-time execution updates."""
    user = await get_user_from_token(token, db)
    if not user:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Verify execution ownership via task
    from app.models.execution import Execution
    result = await db.execute(
        select(Execution)
        .join(Execution.task)
        .where(Execution.id == execution_id, Task.user_id == user.id)
    )
    execution = result.scalar_one_or_none()
    if not execution:
        await websocket.close(code=4004, reason="Execution not found")
        return

    await manager.connect(websocket, user.id)

    try:
        await websocket.send_json({
            "type": "execution_state",
            "execution_id": execution.id,
            "status": execution.status.value,
        })

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id)
    except Exception as e:
        manager.disconnect(websocket, user.id)
        await websocket.close(code=4000, reason=str(e))


# Utility functions for sending updates from background tasks
async def send_task_update(user_id: int, task_id: int, update: dict):
    """Send task update to user."""
    message = {
        "type": "task_update",
        "task_id": task_id,
        **update,
    }
    await manager.send_personal_message(message, user_id)


async def send_execution_update(user_id: int, execution_id: int, update: dict):
    """Send execution update to user."""
    message = {
        "type": "execution_update",
        "execution_id": execution_id,
        **update,
    }
    await manager.send_personal_message(message, user_id)


async def broadcast_system_message(message: dict):
    """Broadcast message to all connected users."""
    await manager.broadcast(message)