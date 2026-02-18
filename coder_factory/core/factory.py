"""
Coder-Factory 核心工厂类
协调整个代码生成流程

底层使用 Claude Code 完成实际工作
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from .state import StateManager
from ..engines.requirement_parser import RequirementParser, ParseResult
from ..engines.claude_client import ClaudeCodeClient
from ..models.requirement import Requirement, TaskType


@dataclass
class ProcessResult:
    """处理结果"""
    success: bool
    message: str
    requirement: Optional[Requirement] = None
    output_path: Optional[str] = None
    error: Optional[str] = None


class CoderFactory:
    """
    AI自主代码工厂

    底层使用 Claude Code 完成:
    - 需求解析
    - 代码生成
    - 测试执行
    - 部署操作

    本类作为编排层，协调完整的生产流程
    """

    def __init__(self, output_dir: str = "./workspace"):
        self.output_dir = Path(output_dir)
        self.state = StateManager()
        self.parser = RequirementParser(self.output_dir)
        self.claude = ClaudeCodeClient(self.output_dir)
        self._current_requirement: Optional[Requirement] = None
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """确保输出目录存在"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_requirement(self, requirement: str) -> ProcessResult:
        """
        处理用户需求的主入口

        Args:
            requirement: 用户的自然语言需求描述

        Returns:
            ProcessResult: 处理结果
        """
        # Step 1: 解析需求
        parse_result = self.parser.parse(requirement)

        if not parse_result.success:
            return ProcessResult(
                success=False,
                message="需求解析失败",
                error=parse_result.error
            )

        self._current_requirement = parse_result.requirement

        return ProcessResult(
            success=True,
            message=f"需求已解析: {parse_result.requirement.summary}",
            requirement=parse_result.requirement,
            output_path=str(self.output_dir)
        )

    def get_task_summary(self) -> dict:
        """获取当前需求的任务摘要"""
        if not self._current_requirement:
            return {"error": "没有当前需求"}

        req = self._current_requirement
        tasks = req.get_all_tasks()

        return {
            "summary": req.summary,
            "project_type": req.project_type,
            "features": req.features,
            "total_tasks": len(tasks),
            "by_priority": {
                "P0": len([t for t in tasks if t.priority.value == "P0"]),
                "P1": len([t for t in tasks if t.priority.value == "P1"]),
                "P2": len([t for t in tasks if t.priority.value == "P2"]),
                "P3": len([t for t in tasks if t.priority.value == "P3"]),
            },
            "by_type": {
                t.value: len([x for x in tasks if x.task_type == t])
                for t in [
                    TaskType.SETUP, TaskType.FRONTEND, TaskType.BACKEND,
                    TaskType.DATABASE, TaskType.API, TaskType.TESTING,
                    TaskType.DEPLOYMENT
                ]
            },
            "clarification_questions": req.clarification_questions,
        }

    def generate_code(self, confirm: bool = True) -> ProcessResult:
        """
        生成代码

        Args:
            confirm: 是否需要用户确认后生成

        Returns:
            ProcessResult: 生成结果
        """
        if not self._current_requirement:
            return ProcessResult(
                success=False,
                message="没有当前需求",
                error="请先调用 process_requirement"
            )

        # 构建项目规格
        spec = self._build_project_spec()

        # 调用 Claude Code 生成代码
        result = self.claude.generate_code(spec, str(self.output_dir))

        if result.success:
            return ProcessResult(
                success=True,
                message="代码生成完成",
                output_path=str(self.output_dir)
            )
        else:
            return ProcessResult(
                success=False,
                message="代码生成失败",
                error=result.error
            )

    def run_tests(self) -> ProcessResult:
        """运行测试"""
        result = self.claude.run_tests(str(self.output_dir))

        return ProcessResult(
            success=result.success,
            message="测试执行完成" if result.success else "测试失败",
            error=result.error
        )

    def deploy(self, method: str = "docker") -> ProcessResult:
        """执行部署"""
        result = self.claude.deploy(str(self.output_dir), method)

        return ProcessResult(
            success=result.success,
            message="部署完成" if result.success else "部署失败",
            error=result.error
        )

    def _build_project_spec(self) -> dict:
        """构建项目规格"""
        if not self._current_requirement:
            return {}

        req = self._current_requirement
        tech_stack = req.metadata.get("suggested_tech_stack")

        return {
            "name": req.project_type,
            "description": req.summary,
            "features": req.features,
            "constraints": req.constraints,
            "tech_stack": tech_stack.to_dict() if tech_stack else None,
            "tasks": [t.to_dict() for t in req.get_all_tasks()],
        }

    # 以下方法保留用于未来扩展
    def confirm_with_user(self, tasks: dict) -> bool:
        """与用户确认任务分解"""
        raise NotImplementedError("F002 - 交互确认系统待实现")

    def design_architecture(self, tasks: dict) -> dict:
        """设计系统架构"""
        raise NotImplementedError("F003 - 架构设计引擎待实现")
