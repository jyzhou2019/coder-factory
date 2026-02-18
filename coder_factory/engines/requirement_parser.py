"""
需求解析引擎 (F001)

使用 Claude Code 解析用户需求，生成任务分解树
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from ..models.requirement import (
    Requirement,
    TaskNode,
    TaskType,
    TaskPriority,
    TaskStatus,
)
from ..models.project_spec import TechStack, Runtime, FrontendFramework, BackendFramework, DatabaseType
from .claude_client import ClaudeCodeClient


# 类型映射表
TASK_TYPE_MAP = {
    "setup": TaskType.SETUP,
    "frontend": TaskType.FRONTEND,
    "backend": TaskType.BACKEND,
    "database": TaskType.DATABASE,
    "api": TaskType.API,
    "testing": TaskType.TESTING,
    "deployment": TaskType.DEPLOYMENT,
    "docs": TaskType.DOCUMENTATION,
    "integration": TaskType.INTEGRATION,
}

PRIORITY_MAP = {
    "P0": TaskPriority.CRITICAL,
    "P1": TaskPriority.HIGH,
    "P2": TaskPriority.MEDIUM,
    "P3": TaskPriority.LOW,
}

RUNTIME_MAP = {
    "python": Runtime.PYTHON,
    "nodejs": Runtime.NODEJS,
    "node": Runtime.NODEJS,
    "go": Runtime.GO,
    "rust": Runtime.RUST,
    "java": Runtime.JAVA,
}

FRONTEND_MAP = {
    "react": FrontendFramework.REACT,
    "vue": FrontendFramework.VUE,
    "svelte": FrontendFramework.SVELTE,
    "nextjs": FrontendFramework.NEXTJS,
    "nuxt": FrontendFramework.NUXT,
    "none": FrontendFramework.NONE,
}

BACKEND_MAP = {
    "fastapi": BackendFramework.FASTAPI,
    "django": BackendFramework.DJANGO,
    "flask": BackendFramework.FLASK,
    "express": BackendFramework.EXPRESS,
    "nestjs": BackendFramework.NESTJS,
    "gin": BackendFramework.GO_GIN,
    "none": BackendFramework.NONE,
}

DATABASE_MAP = {
    "postgresql": DatabaseType.POSTGRESQL,
    "postgres": DatabaseType.POSTGRESQL,
    "mysql": DatabaseType.MYSQL,
    "mongodb": DatabaseType.MONGODB,
    "sqlite": DatabaseType.SQLITE,
    "redis": DatabaseType.REDIS,
    "none": DatabaseType.NONE,
}


@dataclass
class ParseResult:
    """解析结果"""
    success: bool
    requirement: Optional[Requirement] = None
    error: Optional[str] = None


class RequirementParser:
    """
    需求解析引擎

    核心功能：
    1. 调用 Claude Code 解析自然语言需求
    2. 构建任务分解树
    3. 生成澄清问题列表
    """

    def __init__(self, workspace: Path | str = "./workspace"):
        self.client = ClaudeCodeClient(workspace)

    def parse(self, raw_requirement: str) -> ParseResult:
        """
        解析用户需求

        Args:
            raw_requirement: 用户原始需求描述

        Returns:
            ParseResult: 解析结果，包含 Requirement 对象
        """
        # 调用 Claude Code 解析需求
        parsed = self.client.parse_requirement(raw_requirement)

        if "error" in parsed and parsed.get("error"):
            return ParseResult(
                success=False,
                error=parsed.get("error")
            )

        # 构建 Requirement 对象
        requirement = Requirement(
            raw_text=raw_requirement,
            summary=parsed.get("summary", ""),
            project_type=parsed.get("project_type", "unknown"),
            features=parsed.get("features", []),
            constraints=parsed.get("constraints", []),
            clarification_questions=[
                {"question": q, "answered": False}
                for q in parsed.get("questions", [])
            ],
        )

        # 构建任务分解树
        task_tree = self._build_task_tree(parsed.get("tasks", []))
        requirement.task_tree = task_tree

        # 提取技术栈建议
        if "suggested_tech_stack" in parsed:
            requirement.metadata["suggested_tech_stack"] = self._parse_tech_stack(
                parsed["suggested_tech_stack"]
            )

        return ParseResult(
            success=True,
            requirement=requirement
        )

    def _build_task_tree(self, tasks_data: list[dict]) -> TaskNode:
        """
        构建任务分解树

        Args:
            tasks_data: Claude Code 返回的任务列表

        Returns:
            TaskNode: 根任务节点
        """
        # 创建根节点
        root = TaskNode(
            title="项目根任务",
            description="项目开发的顶层任务节点",
            task_type=TaskType.SETUP,
            priority=TaskPriority.CRITICAL,
        )

        for task_data in tasks_data:
            task = TaskNode(
                title=task_data.get("title", "未命名任务"),
                description=task_data.get("description", ""),
                task_type=TASK_TYPE_MAP.get(
                    task_data.get("type", "unknown"),
                    TaskType.UNKNOWN
                ),
                priority=PRIORITY_MAP.get(
                    task_data.get("priority", "P2"),
                    TaskPriority.MEDIUM
                ),
                estimated_complexity=self._estimate_complexity(task_data),
            )

            # 添加子任务
            for subtask_title in task_data.get("subtasks", []):
                subtask = TaskNode(
                    title=subtask_title,
                    task_type=task.task_type,
                    priority=task.priority,
                    estimated_complexity=1,
                )
                task.add_subtask(subtask)

            root.add_subtask(task)

        return root

    def _estimate_complexity(self, task_data: dict) -> int:
        """估算任务复杂度"""
        # 基于子任务数量和描述长度估算
        subtask_count = len(task_data.get("subtasks", []))
        desc_length = len(task_data.get("description", ""))

        complexity = 1
        if subtask_count > 3:
            complexity += 1
        if subtask_count > 5:
            complexity += 1
        if desc_length > 100:
            complexity += 1
        if desc_length > 300:
            complexity += 1

        return min(complexity, 5)

    def _parse_tech_stack(self, tech_data: dict) -> TechStack:
        """解析技术栈建议"""
        return TechStack(
            runtime=RUNTIME_MAP.get(
                tech_data.get("runtime", "python"),
                Runtime.PYTHON
            ),
            frontend=FRONTEND_MAP.get(
                tech_data.get("frontend", "none"),
                FrontendFramework.NONE
            ),
            backend=BACKEND_MAP.get(
                tech_data.get("backend", "fastapi"),
                BackendFramework.FASTAPI
            ),
            database=DATABASE_MAP.get(
                tech_data.get("database", "sqlite"),
                DatabaseType.SQLITE
            ),
        )

    def quick_parse(self, requirement: str) -> dict:
        """
        快速解析 - 仅返回基本信息，不构建完整对象

        用于快速需求预览
        """
        result = self.parse(requirement)
        if result.success and result.requirement:
            return {
                "success": True,
                "summary": result.requirement.summary,
                "project_type": result.requirement.project_type,
                "feature_count": len(result.requirement.features),
                "task_count": len(result.requirement.get_all_tasks()),
                "questions": result.requirement.clarification_questions,
            }
        return {
            "success": False,
            "error": result.error,
        }
