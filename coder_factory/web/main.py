"""
FastAPI Main Application

Entry point for the Coder-Factory Web Interface
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import config
from .services.storage import StorageService
from .services.session_manager import SessionManager

# Import routers
from .routers import (
    requirements,
    dialog,
    architecture,
    codegen,
    deployment,
    delivery,
    tasks,
    websocket,
)


# Global services
storage: StorageService
session_manager: SessionManager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events"""
    global storage, session_manager

    # Startup
    config.ensure_dirs()
    storage = StorageService(config.database_url)
    await storage.init_db()
    session_manager = SessionManager(storage)

    # Store in app state
    app.state.storage = storage
    app.state.session_manager = session_manager

    yield

    # Shutdown
    await storage.close()


# Create FastAPI app
app = FastAPI(
    title="Coder-Factory",
    description="AI-Powered Code Generation Factory Web Interface",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(requirements.router, prefix="/api/requirements", tags=["Requirements"])
app.include_router(dialog.router, prefix="/api/dialog", tags=["Dialog"])
app.include_router(architecture.router, prefix="/api/architecture", tags=["Architecture"])
app.include_router(codegen.router, prefix="/api/codegen", tags=["Code Generation"])
app.include_router(deployment.router, prefix="/api/deployment", tags=["Deployment"])
app.include_router(delivery.router, prefix="/api/delivery", tags=["Delivery"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/", response_class=FileResponse)
async def root():
    """Serve the main HTML page"""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Coder-Factory API", "docs": "/docs"}


@app.get("/api/health")
async def health_check(request: Request):
    """Health check endpoint"""
    storage = getattr(request.app.state, 'storage', None)
    session_manager = getattr(request.app.state, 'session_manager', None)
    return {
        "status": "healthy",
        "version": "0.1.0",
        "services": {
            "storage": "ok" if storage else "not initialized",
            "session_manager": "ok" if session_manager else "not initialized",
        }
    }


@app.get("/api/stats")
async def get_stats(request: Request):
    """Get system statistics"""
    storage = getattr(request.app.state, 'storage', None)
    if not storage:
        return {"error": "Storage not initialized"}

    return await storage.get_stats()
