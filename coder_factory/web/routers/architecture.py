"""
Architecture API Router (F003)

Handles architecture design and visualization
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from ..services.session_manager import SessionManager

router = APIRouter()


class ArchitectureDesign(BaseModel):
    """Architecture design model"""
    session_id: str
    components: List[Dict[str, Any]]
    tech_stack: Dict[str, str]
    api_endpoints: List[Dict[str, str]]
    directory_structure: Dict[str, Any]


def get_session_manager(request: Request) -> SessionManager:
    """Get session manager from app state"""
    return request.app.state.session_manager


@router.post("/design")
async def design_architecture(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Design architecture for approved requirement

    Generates:
        - Component diagram
        - Tech stack details
        - API endpoints
        - Directory structure
    """
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    status = await session_manager.get_flow_status(session_id)
    if status.get("state") != "approved":
        raise HTTPException(
            status_code=400,
            detail="Requirement must be approved first"
        )

    # Get requirement data
    requirement = status.get("requirement", {})

    # Generate architecture design
    architecture = {
        "session_id": session_id,
        "components": _generate_components(requirement),
        "tech_stack": _extract_tech_stack(requirement),
        "api_endpoints": _generate_api_endpoints(requirement),
        "directory_structure": _generate_directory_structure(requirement),
        "component_diagram": _generate_component_diagram_svg(requirement),
    }

    return architecture


@router.get("/{session_id}")
async def get_architecture(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get architecture design for a session"""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    status = await session_manager.get_flow_status(session_id)
    requirement = status.get("requirement", {})

    return {
        "session_id": session_id,
        "tech_stack": _extract_tech_stack(requirement),
        "components": _generate_components(requirement),
        "api_endpoints": _generate_api_endpoints(requirement),
        "directory_structure": _generate_directory_structure(requirement),
    }


@router.get("/tech-info")
async def get_tech_info():
    """
    Get available technology stack options

    Returns all supported technologies and their descriptions
    """
    return {
        "runtimes": {
            "python": {"version": "3.11+", "description": "Python runtime"},
            "nodejs": {"version": "18+", "description": "Node.js runtime"},
            "go": {"version": "1.21+", "description": "Go runtime"},
            "rust": {"version": "1.70+", "description": "Rust runtime"},
        },
        "frontend_frameworks": {
            "react": {"description": "React - A JavaScript library for building UIs"},
            "vue": {"description": "Vue.js - Progressive JavaScript framework"},
            "svelte": {"description": "Svelte - Cybernetically enhanced web apps"},
            "nextjs": {"description": "Next.js - React framework with SSR"},
            "none": {"description": "No frontend (API only)"},
        },
        "backend_frameworks": {
            "fastapi": {"description": "FastAPI - Modern Python web framework"},
            "django": {"description": "Django - Full-featured Python framework"},
            "flask": {"description": "Flask - Lightweight Python framework"},
            "express": {"description": "Express - Node.js web framework"},
            "nestjs": {"description": "NestJS - Progressive Node.js framework"},
            "gin": {"description": "Gin - Go web framework"},
            "none": {"description": "No backend (static only)"},
        },
        "databases": {
            "postgresql": {"description": "PostgreSQL - Advanced open-source database"},
            "mysql": {"description": "MySQL - Popular relational database"},
            "mongodb": {"description": "MongoDB - Document-oriented database"},
            "sqlite": {"description": "SQLite - Lightweight file-based database"},
            "redis": {"description": "Redis - In-memory data store"},
            "none": {"description": "No database"},
        },
    }


def _extract_tech_stack(requirement: dict) -> dict:
    """Extract tech stack from requirement"""
    tech_stack = requirement.get("tech_stack", {})
    if isinstance(tech_stack, dict):
        return tech_stack

    # Default tech stack
    return {
        "runtime": "python",
        "frontend": "none",
        "backend": "fastapi",
        "database": "sqlite",
    }


def _generate_components(requirement: dict) -> list:
    """Generate component list"""
    components = []
    tech_stack = _extract_tech_stack(requirement)
    project_type = requirement.get("project_type", "api")

    # Backend component
    if tech_stack.get("backend") != "none":
        components.append({
            "name": "Backend API",
            "type": "backend",
            "technology": tech_stack.get("backend", "fastapi"),
            "description": "Main API server",
        })

    # Frontend component
    if tech_stack.get("frontend") != "none" and project_type in ["web", "fullstack"]:
        components.append({
            "name": "Frontend",
            "type": "frontend",
            "technology": tech_stack.get("frontend", "react"),
            "description": "User interface",
        })

    # Database component
    if tech_stack.get("database") != "none":
        components.append({
            "name": "Database",
            "type": "database",
            "technology": tech_stack.get("database", "sqlite"),
            "description": "Data persistence layer",
        })

    return components


def _generate_api_endpoints(requirement: dict) -> list:
    """Generate API endpoints based on features"""
    endpoints = []
    features = requirement.get("features", [])

    # Standard CRUD endpoints
    for i, feature in enumerate(features[:5]):  # Limit to first 5 features
        resource = feature.lower().replace(" ", "_")
        endpoints.extend([
            {"method": "GET", "path": f"/api/v1/{resource}", "description": f"List {feature}"},
            {"method": "POST", "path": f"/api/v1/{resource}", "description": f"Create {feature}"},
            {"method": "GET", "path": f"/api/v1/{resource}/{{id}}", "description": f"Get {feature} by ID"},
            {"method": "PUT", "path": f"/api/v1/{resource}/{{id}}", "description": f"Update {feature}"},
            {"method": "DELETE", "path": f"/api/v1/{resource}/{{id}}", "description": f"Delete {feature}"},
        ])

    # Health check endpoint
    endpoints.insert(0, {"method": "GET", "path": "/api/health", "description": "Health check"})

    return endpoints


def _generate_directory_structure(requirement: dict) -> dict:
    """Generate project directory structure"""
    tech_stack = _extract_tech_stack(requirement)
    project_type = requirement.get("project_type", "api")

    structure = {
        "name": "project",
        "type": "directory",
        "children": []
    }

    # Backend structure
    if tech_stack.get("backend") == "fastapi":
        structure["children"].append({
            "name": "app",
            "type": "directory",
            "children": [
                {"name": "__init__.py", "type": "file"},
                {"name": "main.py", "type": "file"},
                {"name": "routers", "type": "directory", "children": []},
                {"name": "models", "type": "directory", "children": []},
                {"name": "schemas", "type": "directory", "children": []},
                {"name": "services", "type": "directory", "children": []},
            ]
        })

    # Frontend structure
    if tech_stack.get("frontend") != "none" and project_type in ["web", "fullstack"]:
        structure["children"].append({
            "name": "frontend",
            "type": "directory",
            "children": [
                {"name": "src", "type": "directory", "children": [
                    {"name": "components", "type": "directory"},
                    {"name": "pages", "type": "directory"},
                    {"name": "App.tsx", "type": "file"},
                ]},
                {"name": "package.json", "type": "file"},
            ]
        })

    # Common files
    structure["children"].extend([
        {"name": "requirements.txt", "type": "file"},
        {"name": "Dockerfile", "type": "file"},
        {"name": "docker-compose.yml", "type": "file"},
        {"name": "README.md", "type": "file"},
        {"name": ".env.example", "type": "file"},
    ])

    return structure


def _generate_component_diagram_svg(requirement: dict) -> str:
    """Generate simple SVG component diagram"""
    components = _generate_components(requirement)

    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400">',
        '  <style>',
        '    .box { fill: #e3f2fd; stroke: #1976d2; stroke-width: 2; }',
        '    .label { font-family: Arial; font-size: 14px; text-anchor: middle; }',
        '    .arrow { stroke: #666; stroke-width: 2; fill: none; marker-end: url(#arrow); }',
        '  </style>',
        '  <defs>',
        '    <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">',
        '      <path d="M0,0 L0,6 L9,3 z" fill="#666"/>',
        '    </marker>',
        '  </defs>',
    ]

    # Draw components
    x_positions = [100, 300, 500, 700]
    for i, comp in enumerate(components[:4]):
        x = x_positions[i]
        y = 150
        svg_parts.append(f'  <rect x="{x}" y="{y}" width="120" height="60" rx="8" class="box"/>')
        svg_parts.append(f'  <text x="{x + 60}" y="{y + 35}" class="label">{comp["name"]}</text>')

        # Draw connection arrows
        if i > 0:
            prev_x = x_positions[i - 1] + 120
            svg_parts.append(f'  <line x1="{prev_x}" y1="180" x2="{x}" y2="180" class="arrow"/>')

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)
