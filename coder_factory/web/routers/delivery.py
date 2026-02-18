"""
Delivery API Router (F007)

Handles documentation generation and release preparation
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime

from ..services.session_manager import SessionManager
from ..services.storage import StorageService

router = APIRouter()


class DocsRequest(BaseModel):
    """Documentation generation request"""
    session_id: str
    types: Optional[List[str]] = None  # readme, changelog, api, deployment


class ReleaseRequest(BaseModel):
    """Release preparation request"""
    session_id: str
    version: Optional[str] = None
    changelog: Optional[str] = None


def get_session_manager(request: Request) -> SessionManager:
    """Get session manager from app state"""
    return request.app.state.session_manager


def get_storage(request: Request) -> StorageService:
    """Get storage service from app state"""
    return request.app.state.storage


@router.get("/checklist")
async def get_delivery_checklist(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get delivery checklist for a project

    Returns a checklist of items to verify before delivery
    """
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    status = await session_manager.get_flow_status(session_id)
    requirement = status.get("requirement", {})

    checklist = [
        {"id": "code", "name": "Source Code", "status": "pending", "required": True},
        {"id": "tests", "name": "Unit Tests", "status": "pending", "required": True},
        {"id": "readme", "name": "README.md", "status": "pending", "required": True},
        {"id": "dockerfile", "name": "Dockerfile", "status": "pending", "required": False},
        {"id": "compose", "name": "docker-compose.yml", "status": "pending", "required": False},
        {"id": "env_example", "name": ".env.example", "status": "pending", "required": True},
        {"id": "requirements", "name": "requirements.txt", "status": "pending", "required": True},
        {"id": "changelog", "name": "CHANGELOG.md", "status": "pending", "required": False},
        {"id": "api_docs", "name": "API Documentation", "status": "pending", "required": False},
    ]

    return {
        "session_id": session_id,
        "project_name": requirement.get("project_type", "project"),
        "checklist": checklist,
        "completion_percentage": 0,
    }


@router.post("/docs")
async def generate_docs(
    request: DocsRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Generate documentation for the project

    Generates:
        - README.md
        - CHANGELOG.md
        - API documentation
        - Deployment guide
    """
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    status = await session_manager.get_flow_status(request.session_id)
    requirement = status.get("requirement", {})

    doc_types = request.types or ["readme", "changelog", "api", "deployment"]
    generated_docs = {}

    if "readme" in doc_types:
        generated_docs["README.md"] = _generate_readme(requirement)

    if "changelog" in doc_types:
        generated_docs["CHANGELOG.md"] = _generate_changelog(requirement)

    if "api" in doc_types:
        generated_docs["API.md"] = _generate_api_docs(requirement)

    if "deployment" in doc_types:
        generated_docs["DEPLOYMENT.md"] = _generate_deployment_guide(requirement)

    return {
        "session_id": request.session_id,
        "generated": list(generated_docs.keys()),
        "docs": generated_docs,
    }


@router.post("/release")
async def prepare_release(
    request: ReleaseRequest,
    session_manager: SessionManager = Depends(get_session_manager),
    storage: StorageService = Depends(get_storage)
):
    """
    Prepare project for release

    Creates release package with version bump
    """
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    status = await session_manager.get_flow_status(request.session_id)
    requirement = status.get("requirement", {})

    version = request.version or "1.0.0"

    # Record delivered project
    await storage.create_delivered_project(
        str(uuid.uuid4()),
        request.session_id,
        name=requirement.get("project_type", "project"),
        description=requirement.get("summary", ""),
        output_path=f"./workspace/{request.session_id}",
        tech_stack=requirement.get("tech_stack", {}),
    )

    return {
        "session_id": request.session_id,
        "version": version,
        "status": "ready",
        "release_notes": request.changelog or "Initial release",
        "output_path": f"./workspace/{request.session_id}",
    }


@router.get("/projects")
async def list_delivered_projects(
    storage: StorageService = Depends(get_storage)
):
    """List all delivered projects"""
    projects = await storage.list_delivered_projects()

    return {
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "created_at": p.created_at.isoformat(),
                "tech_stack": p.tech_stack,
            }
            for p in projects
        ]
    }


@router.get("/projects/{project_id}")
async def get_delivered_project(
    project_id: str,
    storage: StorageService = Depends(get_storage)
):
    """Get details of a delivered project"""
    projects = await storage.list_delivered_projects()
    project = next((p for p in projects if p.id == project_id), None)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "output_path": project.output_path,
        "created_at": project.created_at.isoformat(),
        "tech_stack": project.tech_stack,
    }


def _generate_readme(requirement: dict) -> str:
    """Generate README.md content"""
    project_name = requirement.get("project_type", "project")
    summary = requirement.get("summary", "A generated project")
    features = requirement.get("features", [])
    tech_stack = requirement.get("tech_stack", {})

    return f'''# {project_name.title()}

{summary}

## Features

{chr(10).join(f"- {f}" for f in features)}

## Tech Stack

- Runtime: {tech_stack.get("runtime", "python")}
- Backend: {tech_stack.get("backend", "fastapi")}
- Frontend: {tech_stack.get("frontend", "none")}
- Database: {tech_stack.get("database", "sqlite")}

## Getting Started

### Prerequisites

- Python 3.11+
- Docker (optional)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd {project_name}

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m app.main
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up -d
```

## API Endpoints

See [API.md](API.md) for detailed API documentation.

## License

MIT
'''


def _generate_changelog(requirement: dict) -> str:
    """Generate CHANGELOG.md content"""
    project_name = requirement.get("project_type", "project")
    summary = requirement.get("summary", "")

    return f'''# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - {datetime.now().strftime("%Y-%m-%d")}

### Added
- Initial release
- {summary}
'''


def _generate_api_docs(requirement: dict) -> str:
    """Generate API documentation"""
    features = requirement.get("features", [])

    docs = '''# API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Endpoints

'''

    for feature in features[:5]:
        resource = feature.lower().replace(" ", "_")
        docs += f'''### {feature}

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{resource}` | List all {feature} |
| POST | `/{resource}` | Create a new {feature} |
| GET | `/{resource}/{{id}}` | Get {feature} by ID |
| PUT | `/{resource}/{{id}}` | Update {feature} |
| DELETE | `/{resource}/{{id}}` | Delete {feature} |

'''

    return docs


def _generate_deployment_guide(requirement: dict) -> str:
    """Generate deployment guide"""
    tech_stack = requirement.get("tech_stack", {})

    return f'''# Deployment Guide

## Prerequisites

- Docker and Docker Compose
- (Optional) Kubernetes cluster for production

## Quick Start

### Using Docker Compose

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | Database connection URL | sqlite:///./data/app.db |
| DEBUG | Enable debug mode | false |

## Production Deployment

### Docker

1. Build the image:
   ```bash
   docker build -t {requirement.get("project_type", "app")}:latest .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 {requirement.get("project_type", "app")}:latest
   ```

### Health Check

The application exposes a health check endpoint:

```bash
curl http://localhost:8000/api/health
```

## Monitoring

- Health endpoint: `/api/health`
- Metrics: (configure as needed)

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in docker-compose.yml
2. **Database connection failed**: Check DATABASE_URL environment variable

## Support

For issues and feature requests, please create an issue in the repository.
'''
