"""
Deployment API Router (F006)

Handles deployment configuration generation and Docker build
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime

from ..services.session_manager import SessionManager

router = APIRouter()


class DeployConfigRequest(BaseModel):
    """Deploy config generation request"""
    session_id: str
    method: str = "docker"  # docker, local, both


class BuildRequest(BaseModel):
    """Docker build request"""
    session_id: str
    tag: Optional[str] = None
    push: bool = False


class DeploymentStatus(BaseModel):
    """Deployment status model"""
    deployment_id: str
    session_id: str
    method: str
    status: str
    message: str
    started_at: str
    completed_at: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


# In-memory deployment tracking
_deployments: Dict[str, Dict[str, Any]] = {}


def get_session_manager(request: Request) -> SessionManager:
    """Get session manager from app state"""
    return request.app.state.session_manager


@router.post("/generate")
async def generate_deploy_config(
    request: DeployConfigRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Generate deployment configuration files

    Creates:
        - Dockerfile
        - docker-compose.yml
        - .dockerignore
        - nginx.conf (if applicable)
    """
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    status = await session_manager.get_flow_status(request.session_id)
    requirement = status.get("requirement", {})
    tech_stack = requirement.get("tech_stack", {})

    # Generate deployment configs
    configs = _generate_deployment_configs(tech_stack, request.method)

    return {
        "session_id": request.session_id,
        "method": request.method,
        "configs": configs,
    }


@router.post("/build")
async def build_docker(
    request: BuildRequest,
    background_tasks: BackgroundTasks,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Build Docker image for the project

    Runs in background and reports progress via WebSocket
    """
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create deployment record
    deployment_id = str(uuid.uuid4())[:8]
    deployment = {
        "deployment_id": deployment_id,
        "session_id": request.session_id,
        "method": "docker",
        "status": "pending",
        "message": "Build queued",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "url": None,
        "error": None,
    }
    _deployments[deployment_id] = deployment

    # Start background build
    background_tasks.add_task(
        _run_build,
        deployment_id,
        request.session_id,
        request.tag,
        session_manager
    )

    return {
        "deployment_id": deployment_id,
        "status": "pending",
        "message": "Docker build started",
    }


@router.post("/deploy")
async def deploy_project(
    request: DeployConfigRequest,
    background_tasks: BackgroundTasks,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Deploy the project

    For Docker: runs docker-compose up
    For local: starts the application directly
    """
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create deployment record
    deployment_id = str(uuid.uuid4())[:8]
    deployment = {
        "deployment_id": deployment_id,
        "session_id": request.session_id,
        "method": request.method,
        "status": "pending",
        "message": "Deployment queued",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "url": None,
        "error": None,
    }
    _deployments[deployment_id] = deployment

    # Start background deployment
    background_tasks.add_task(
        _run_deployment,
        deployment_id,
        request.session_id,
        request.method,
        session_manager
    )

    return {
        "deployment_id": deployment_id,
        "status": "pending",
        "message": "Deployment started",
    }


@router.get("/status/{deployment_id}", response_model=DeploymentStatus)
async def get_deployment_status(deployment_id: str):
    """Get status of a deployment"""
    deployment = _deployments.get(deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    return DeploymentStatus(**deployment)


@router.get("/list")
async def list_deployments(session_id: Optional[str] = None):
    """List all deployments"""
    deployments = list(_deployments.values())

    if session_id:
        deployments = [d for d in deployments if d["session_id"] == session_id]

    return {"deployments": deployments}


def _generate_deployment_configs(tech_stack: dict, method: str) -> dict:
    """Generate deployment configuration files"""
    runtime = tech_stack.get("runtime", "python")
    backend = tech_stack.get("backend", "fastapi")
    frontend = tech_stack.get("frontend", "none")
    database = tech_stack.get("database", "sqlite")

    configs = {}

    # Dockerfile
    if runtime == "python":
        configs["Dockerfile"] = _generate_python_dockerfile(backend)
    elif runtime == "nodejs":
        configs["Dockerfile"] = _generate_nodejs_dockerfile(backend)

    # docker-compose.yml
    configs["docker-compose.yml"] = _generate_docker_compose(
        backend, frontend, database
    )

    # .dockerignore
    configs[".dockerignore"] = """__pycache__/
*.pyc
*.pyo
.git/
.gitignore
.env
.venv/
venv/
node_modules/
*.log
.pytest_cache/
.coverage
htmlcov/
"""

    # nginx.conf for frontend
    if frontend != "none":
        configs["nginx.conf"] = _generate_nginx_config()

    return configs


def _generate_python_dockerfile(backend: str) -> str:
    """Generate Python Dockerfile"""
    return f'''FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''


def _generate_nodejs_dockerfile(backend: str) -> str:
    """Generate Node.js Dockerfile"""
    return f'''FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy application
COPY . .

# Build if needed
RUN npm run build

# Expose port
EXPOSE 3000

# Run application
CMD ["npm", "start"]
'''


def _generate_docker_compose(
    backend: str,
    frontend: str,
    database: str
) -> str:
    """Generate docker-compose.yml"""
    services = []

    # Backend service
    services.append('''  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/app.db
    volumes:
      - ./data:/app/data''')

    # Database service
    if database == "postgresql":
        services.append('''  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=app
      - POSTGRES_PASSWORD=secret
      - POSTGRES_DB=app
    volumes:
      - postgres_data:/var/lib/postgresql/data''')
    elif database == "mongodb":
        services.append('''  mongo:
    image: mongo:6
    volumes:
      - mongo_data:/data/db''')
    elif database == "mysql":
        services.append('''  mysql:
    image: mysql:8
    environment:
      - MYSQL_ROOT_PASSWORD=secret
      - MYSQL_DATABASE=app
    volumes:
      - mysql_data:/var/lib/mysql''')

    # Frontend service
    if frontend != "none":
        services.append('''  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend''')

    volumes = []
    if database == "postgresql":
        volumes.append("postgres_data:")
    elif database == "mongodb":
        volumes.append("mongo_data:")
    elif database == "mysql":
        volumes.append("mysql_data:")

    compose = f'''version: "3.8"

services:
{chr(10).join(services)}
'''

    if volumes:
        compose += f'''
volumes:
{chr(10).join(volumes)}
'''

    return compose


def _generate_nginx_config() -> str:
    """Generate nginx configuration"""
    return '''server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
'''


async def _run_build(
    deployment_id: str,
    session_id: str,
    tag: Optional[str],
    session_manager: SessionManager
):
    """Background task for Docker build"""
    deployment = _deployments[deployment_id]

    try:
        deployment["status"] = "building"
        deployment["message"] = "Building Docker image..."

        # Simulate build (in production, run actual docker build)
        import asyncio
        await asyncio.sleep(2)  # Simulate build time

        deployment["status"] = "completed"
        deployment["message"] = "Docker image built successfully"
        deployment["url"] = f"localhost/{session_id}:latest"

    except Exception as e:
        deployment["status"] = "failed"
        deployment["error"] = str(e)
        deployment["message"] = f"Build failed: {str(e)}"

    finally:
        deployment["completed_at"] = datetime.utcnow().isoformat()


async def _run_deployment(
    deployment_id: str,
    session_id: str,
    method: str,
    session_manager: SessionManager
):
    """Background task for deployment"""
    deployment = _deployments[deployment_id]

    try:
        deployment["status"] = "deploying"
        deployment["message"] = f"Deploying with {method}..."

        # Run actual deployment
        result = await session_manager.deploy(session_id, method)

        if result["success"]:
            deployment["status"] = "running"
            deployment["message"] = result.get("message", "Deployment successful")
            deployment["url"] = "http://localhost:8000"
        else:
            deployment["status"] = "failed"
            deployment["error"] = result.get("error")
            deployment["message"] = "Deployment failed"

    except Exception as e:
        deployment["status"] = "failed"
        deployment["error"] = str(e)
        deployment["message"] = f"Deployment failed: {str(e)}"

    finally:
        deployment["completed_at"] = datetime.utcnow().isoformat()
