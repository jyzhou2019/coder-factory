"""
Tasks API Router

Handles task management and status tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..services.session_manager import SessionManager
from ..services.storage import StorageService

router = APIRouter()


def get_session_manager(request: Request) -> SessionManager:
    """Get session manager from app state"""
    return request.app.state.session_manager


def get_storage(request: Request) -> StorageService:
    """Get storage service from app state"""
    return request.app.state.storage


@router.get("")
async def list_tasks(
    session_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    storage: StorageService = Depends(get_storage)
):
    """
    List all tasks

    Supports filtering by:
        - session_id: Filter by session
        - status: Filter by task status (pending, in_progress, completed, etc.)
    """
    tasks = await storage.list_tasks(session_id=session_id, status=status, limit=limit)

    return {
        "tasks": [
            {
                "id": t.id,
                "session_id": t.session_id,
                "title": t.title,
                "description": t.description,
                "task_type": t.task_type,
                "priority": t.priority,
                "status": t.status,
                "progress": t.progress,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat(),
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in tasks
        ],
        "count": len(tasks),
    }


@router.get("/running")
async def get_running_tasks(
    storage: StorageService = Depends(get_storage)
):
    """Get all currently running tasks"""
    tasks = await storage.get_running_tasks()

    return {
        "running_tasks": [
            {
                "id": t.id,
                "session_id": t.session_id,
                "title": t.title,
                "task_type": t.task_type,
                "progress": t.progress,
                "started_at": t.updated_at.isoformat(),
            }
            for t in tasks
        ],
        "count": len(tasks),
    }


@router.get("/stats")
async def get_task_stats(
    storage: StorageService = Depends(get_storage)
):
    """
    Get task statistics

    Returns:
        - Total tasks
        - Tasks by status
        - Tasks by priority
        - Tasks by type
    """
    all_tasks = await storage.list_tasks(limit=1000)

    stats = {
        "total": len(all_tasks),
        "by_status": {},
        "by_priority": {},
        "by_type": {},
    }

    for task in all_tasks:
        # By status
        status = task.status
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

        # By priority
        priority = task.priority
        stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1

        # By type
        task_type = task.task_type
        stats["by_type"][task_type] = stats["by_type"].get(task_type, 0) + 1

    return stats


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    storage: StorageService = Depends(get_storage)
):
    """Get task details by ID"""
    task = await storage.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "id": task.id,
        "session_id": task.session_id,
        "title": task.title,
        "description": task.description,
        "task_type": task.task_type,
        "priority": task.priority,
        "status": task.status,
        "progress": task.progress,
        "parent_id": task.parent_id,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


@router.patch("/{task_id}")
async def update_task(
    task_id: str,
    status: Optional[str] = None,
    progress: Optional[int] = None,
    storage: StorageService = Depends(get_storage)
):
    """Update task status or progress"""
    task = await storage.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = {}
    if status is not None:
        updates["status"] = status
    if progress is not None:
        updates["progress"] = min(100, max(0, progress))

    if updates:
        await storage.update_task(task_id, **updates)

    return {"success": True, "task_id": task_id, "updates": updates}


@router.post("/session/{session_id}/create")
async def create_task_for_session(
    session_id: str,
    title: str,
    description: str = "",
    task_type: str = "unknown",
    priority: str = "P2",
    session_manager: SessionManager = Depends(get_session_manager),
    storage: StorageService = Depends(get_storage)
):
    """Create a new task for a session"""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    import uuid
    task_id = str(uuid.uuid4())[:8]

    task = await storage.create_task(
        task_id,
        session_id,
        title=title,
        description=description,
        task_type=task_type,
        priority=priority,
    )

    return {
        "success": True,
        "task": {
            "id": task.id,
            "session_id": task.session_id,
            "title": task.title,
            "status": task.status,
        }
    }


@router.get("/session/{session_id}/summary")
async def get_session_task_summary(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get task summary for a specific session"""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    summary = await session_manager.get_task_summary(session_id)
    return summary
