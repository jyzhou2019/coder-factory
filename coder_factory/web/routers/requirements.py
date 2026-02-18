"""
Requirements API Router (F001)

Handles requirement submission and parsing
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
import uuid

from ..services.session_manager import SessionManager

router = APIRouter()

# Demo mode - set to True if Claude CLI is not available
DEMO_MODE = os.getenv("CODER_FACTORY_DEMO", "false").lower() == "true"


class RequirementInput(BaseModel):
    """Requirement input model"""
    text: str
    session_id: Optional[str] = None
    demo: Optional[bool] = False


class RequirementResponse(BaseModel):
    """Requirement response model"""
    success: bool
    session_id: str
    summary: Optional[str] = None
    project_type: Optional[str] = None
    features: Optional[List[str]] = None
    task_count: Optional[int] = None
    questions: Optional[List[dict]] = None
    error: Optional[str] = None


def get_session_manager(request: Request) -> SessionManager:
    """Get session manager from app state"""
    sm = getattr(request.app.state, 'session_manager', None)
    if sm is None:
        raise HTTPException(status_code=503, detail="Service not ready - please wait for startup")
    return sm


def get_mock_requirement_result(text: str) -> dict:
    """Generate mock requirement parsing result for demo mode"""
    text_lower = text.lower()

    # Detect project type
    if "api" in text_lower or "后端" in text_lower:
        project_type = "api"
        features = [
            "RESTful API接口",
            "用户认证与授权",
            "数据验证",
            "错误处理",
            "API文档自动生成"
        ]
    elif "web" in text_lower or "网站" in text_lower or "页面" in text_lower:
        project_type = "web"
        features = [
            "响应式用户界面",
            "用户登录注册",
            "数据展示与管理",
            "表单验证",
            "状态管理"
        ]
    elif "cli" in text_lower or "命令行" in text_lower:
        project_type = "cli"
        features = [
            "命令行参数解析",
            "交互式提示",
            "配置文件支持",
            "彩色输出",
            "帮助文档"
        ]
    else:
        project_type = "api"
        features = [
            "核心功能模块",
            "数据处理",
            "配置管理",
            "日志记录",
            "错误处理"
        ]

    # Detect if todo/task related
    if "待办" in text_lower or "todo" in text_lower or "任务" in text_lower:
        features = [
            "创建待办事项",
            "查看待办列表",
            "更新待办状态",
            "删除待办事项",
            "分类与标签"
        ]

    return {
        "success": True,
        "state": "confirming",
        "summary": f"检测到{project_type}类型项目需求",
        "project_type": project_type,
        "features": features,
        "constraints": ["使用Python实现", "支持Docker部署"],
        "questions_count": 3,
        "clarification_questions": [
            {"question": "需要支持哪些用户认证方式?", "answered": False},
            {"question": "是否需要数据持久化?", "answered": False},
            {"question": "预期的并发用户数量是多少?", "answered": False}
        ],
        "suggested_tech_stack": {
            "runtime": "python",
            "frontend": "none" if project_type == "api" else "react",
            "backend": "fastapi",
            "database": "sqlite"
        }
    }


@router.post("", response_model=RequirementResponse)
async def submit_requirement(
    requirement: RequirementInput,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Submit and parse a new requirement

    This endpoint:
    1. Creates or uses existing session
    2. Parses the requirement
    3. Returns parsed result with questions
    """
    # Create or get session
    if requirement.session_id:
        session = await session_manager.get_session(requirement.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session_id = requirement.session_id
    else:
        session = await session_manager.create_session()
        session_id = session["session_id"]

    # Use demo/mock mode if requested or if in demo environment
    if DEMO_MODE or requirement.demo:
        result = get_mock_requirement_result(requirement.text)
        return RequirementResponse(
            success=result.get("success", False),
            session_id=session_id,
            summary=result.get("summary"),
            project_type=result.get("project_type"),
            features=result.get("features"),
            task_count=result.get("questions_count"),
            questions=result.get("clarification_questions"),
            error=result.get("error"),
        )

    # Start requirement flow with real Claude CLI
    try:
        result = await session_manager.start_requirement_flow(
            session_id,
            requirement.text
        )
    except Exception as e:
        # Fallback to demo mode if Claude CLI is not available
        if "Claude Code CLI not found" in str(e):
            result = get_mock_requirement_result(requirement.text)
        else:
            raise

    return RequirementResponse(
        success=result.get("success", False),
        session_id=session_id,
        summary=result.get("summary"),
        project_type=result.get("project_type"),
        features=result.get("features"),
        task_count=result.get("questions_count"),
        questions=result.get("clarification_questions"),
        error=result.get("error"),
    )


@router.get("/{session_id}")
async def get_requirement(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get requirement details for a session"""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    status = await session_manager.get_flow_status(session_id)
    return {
        "session_id": session_id,
        "status": session.get("status"),
        "flow_state": status.get("state"),
        "requirement": status.get("requirement"),
    }


@router.get("/{session_id}/tasks")
async def get_requirement_tasks(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get task breakdown for a requirement"""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    summary = await session_manager.get_task_summary(session_id)
    return summary
