"""
需求与任务数据模型
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime
import uuid


class TaskType(Enum):
    """任务类型"""
    SETUP = "setup"              # 项目初始化
    FRONTEND = "frontend"        # 前端开发
    BACKEND = "backend"          # 后端开发
    DATABASE = "database"        # 数据库
    API = "api"                  # API 开发
    TESTING = "testing"          # 测试
    DEPLOYMENT = "deployment"    # 部署
    DOCUMENTATION = "docs"       # 文档
    INTEGRATION = "integration"  # 集成
    UNKNOWN = "unknown"          # 未知


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = "P0"    # 阻塞性，必须立即完成
    HIGH = "P1"        # 高优先级
    MEDIUM = "P2"      # 中优先级
    LOW = "P3"         # 低优先级


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class TaskNode:
    """
    任务节点 - 树形结构

    每个任务可以包含子任务，形成任务分解树
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    task_type: TaskType = TaskType.UNKNOWN
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    dependencies: list[str] = field(default_factory=list)  # 依赖的任务ID列表
    subtasks: list["TaskNode"] = field(default_factory=list)
    estimated_complexity: int = 1  # 1-5 复杂度等级
    acceptance_criteria: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_subtask(self, task: "TaskNode") -> "TaskNode":
        """添加子任务"""
        self.subtasks.append(task)
        return task

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.task_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "subtasks": [t.to_dict() for t in self.subtasks],
            "complexity": self.estimated_complexity,
            "acceptance_criteria": self.acceptance_criteria,
            "metadata": self.metadata,
        }

    def flatten(self) -> list["TaskNode"]:
        """展平为任务列表"""
        result = [self]
        for subtask in self.subtasks:
            result.extend(subtask.flatten())
        return result

    def get_total_complexity(self) -> int:
        """计算总复杂度"""
        return self.estimated_complexity + sum(
            t.get_total_complexity() for t in self.subtasks
        )


@dataclass
class Requirement:
    """
    用户需求

    存储原始需求和解析后的结构化信息
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    raw_text: str = ""                           # 用户原始输入
    summary: str = ""                            # 需求摘要
    project_type: str = ""                       # 项目类型 (web/api/cli/etc)
    features: list[str] = field(default_factory=list)  # 核心功能列表
    constraints: list[str] = field(default_factory=list)  # 约束条件
    task_tree: Optional[TaskNode] = None         # 任务分解树
    clarification_questions: list[dict] = field(default_factory=list)  # 待确认问题
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "raw_text": self.raw_text,
            "summary": self.summary,
            "project_type": self.project_type,
            "features": self.features,
            "constraints": self.constraints,
            "task_tree": self.task_tree.to_dict() if self.task_tree else None,
            "clarification_questions": self.clarification_questions,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    def get_all_tasks(self) -> list[TaskNode]:
        """获取所有任务列表"""
        if self.task_tree:
            return self.task_tree.flatten()
        return []
