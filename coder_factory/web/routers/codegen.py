"""
Code Generation API Router (F004/F005)

Handles code generation and job tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

from ..services.session_manager import SessionManager
from ..services.storage import StorageService

router = APIRouter()


class GenerateRequest(BaseModel):
    """Code generation request"""
    session_id: str
    options: Optional[Dict[str, Any]] = None


class JobStatus(BaseModel):
    """Job status model"""
    job_id: str
    session_id: str
    status: str
    progress: int
    message: str
    started_at: str
    completed_at: Optional[str] = None
    output_path: Optional[str] = None
    error: Optional[str] = None


# In-memory job tracking (should be in storage for production)
_jobs: Dict[str, Dict[str, Any]] = {}


def get_session_manager(request: Request) -> SessionManager:
    """Get session manager from app state"""
    return request.app.state.session_manager


def get_storage(request: Request) -> StorageService:
    """Get storage service from app state"""
    return request.app.state.storage


@router.post("/generate")
async def start_generation(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Start code generation for an approved requirement

    This runs in the background and updates via WebSocket
    """
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    status = await session_manager.get_flow_status(request.session_id)
    if status.get("state") != "approved":
        raise HTTPException(
            status_code=400,
            detail="Requirement must be approved first"
        )

    # Create job
    job_id = str(uuid.uuid4())[:8]
    job = {
        "job_id": job_id,
        "session_id": request.session_id,
        "status": "pending",
        "progress": 0,
        "message": "Job queued",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "output_path": None,
        "error": None,
    }
    _jobs[job_id] = job

    # Start background generation
    background_tasks.add_task(
        _run_generation,
        job_id,
        request.session_id,
        session_manager
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Code generation started",
    }


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get status of a code generation job"""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatus(**job)


@router.get("/jobs")
async def list_jobs(
    session_id: Optional[str] = None,
    status: Optional[str] = None
):
    """List all jobs, optionally filtered"""
    jobs = list(_jobs.values())

    if session_id:
        jobs = [j for j in jobs if j["session_id"] == session_id]
    if status:
        jobs = [j for j in jobs if j["status"] == status]

    return {"jobs": jobs}


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Cancel a running job"""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] in ["completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status: {job['status']}"
        )

    job["status"] = "cancelled"
    job["completed_at"] = datetime.utcnow().isoformat()
    job["message"] = "Job cancelled by user"

    return {"success": True, "job_id": job_id, "status": "cancelled"}


async def _run_generation(
    job_id: str,
    session_id: str,
    session_manager: SessionManager
):
    """Background task for code generation"""
    job = _jobs[job_id]

    try:
        # Update status
        job["status"] = "running"
        job["message"] = "Starting code generation..."
        job["progress"] = 10

        # Run actual generation
        result = await session_manager.start_code_generation(session_id)

        if result["success"]:
            job["status"] = "completed"
            job["progress"] = 100
            job["message"] = result.get("message", "Code generation completed")
            job["output_path"] = result.get("output_path")
        else:
            job["status"] = "failed"
            job["error"] = result.get("error", "Unknown error")
            job["message"] = "Code generation failed"

    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["message"] = f"Error: {str(e)}"

    finally:
        job["completed_at"] = datetime.utcnow().isoformat()
