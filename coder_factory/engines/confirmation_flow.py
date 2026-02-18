"""
交互确认协调器

协调 RequirementParser 和 InteractionManager
提供完整的交互式需求确认流程
"""

from typing import Optional
from pathlib import Path

from .interaction_manager import (
    InteractionManager,
    DialogState,
    QuestionType,
    Question,
)
from .requirement_parser import RequirementParser, ParseResult
from .claude_client import ClaudeCodeClient
from ..models.requirement import Requirement, TaskNode


class ConfirmationFlow:
    """
    交互确认流程

    完整的需求确认流程：
    1. 解析需求
    2. 生成确认问题
    3. 收集用户回答
    4. 更新需求
    5. 获得最终批准
    """

    def __init__(self, workspace: Path | str = "./workspace"):
        self.workspace = Path(workspace)
        self.parser = RequirementParser(workspace)
        self.claude = ClaudeCodeClient(workspace)
        self.manager = InteractionManager()
        self._requirement: Optional[Requirement] = None

    def start(self, raw_requirement: str) -> dict:
        """
        开始交互确认流程

        Args:
            raw_requirement: 用户原始需求

        Returns:
            dict: 流程状态和下一步提示
        """
        # 解析需求
        parse_result = self.parser.parse(raw_requirement)

        if not parse_result.success:
            return {
                "success": False,
                "error": parse_result.error,
                "state": "failed",
            }

        self._requirement = parse_result.requirement

        # 启动对话
        initial_data = {
            "raw_text": raw_requirement,
            "summary": self._requirement.summary,
            "project_type": self._requirement.project_type,
            "features": self._requirement.features,
            "constraints": self._requirement.constraints,
            "tech_stack": self._requirement.metadata.get("suggested_tech_stack").to_dict()
            if self._requirement.metadata.get("suggested_tech_stack") else None,
        }

        self.manager.start_dialog(initial_data)
        self.manager.transition_state(DialogState.CONFIRMING)

        # 添加初始对话轮次
        self.manager.add_turn(
            user_input=raw_requirement,
            system_response=f"需求已解析: {self._requirement.summary}"
        )

        # 生成确认问题
        self._generate_confirmation_questions()

        return {
            "success": True,
            "state": "confirming",
            "summary": self._requirement.summary,
            "project_type": self._requirement.project_type,
            "features": self._requirement.features,
            "next_action": "confirm_questions",
            "questions_count": len(self.manager.get_unanswered_questions()),
        }

    def _generate_confirmation_questions(self):
        """根据需求生成确认问题"""
        req = self._requirement
        if not req:
            return

        # 问题1: 确认项目类型
        self.manager.add_question(
            question=f"检测到项目类型为 '{req.project_type}'，是否正确?",
            type=QuestionType.CONFIRM,
            default=True,
            required=True,
        )

        # 问题2: 确认技术栈
        tech_stack = req.metadata.get("suggested_tech_stack")
        if tech_stack:
            self.manager.add_question(
                question=f"建议使用 {tech_stack.runtime.value} 技术栈，是否接受?",
                type=QuestionType.CONFIRM,
                default=True,
                required=True,
            )

        # 问题3: 功能优先级确认
        if len(req.features) > 1:
            feature_list = "\n".join(f"  {i+1}. {f}" for i, f in enumerate(req.features))
            self.manager.add_question(
                question=f"以下功能是否都需要实现?\n{feature_list}",
                type=QuestionType.CONFIRM,
                default=True,
                required=True,
            )

        # 问题4: 数据库选择 (如果需要)
        if req.project_type in ["web", "api"]:
            self.manager.add_question(
                question="请选择数据库类型:",
                type=QuestionType.CHOICE,
                options=["SQLite (轻量级)", "PostgreSQL (生产级)", "MongoDB (文档型)", "MySQL (传统)"],
                default="SQLite (轻量级)",
                required=True,
            )

        # 问题5: 部署方式
        self.manager.add_question(
            question="选择部署方式:",
            type=QuestionType.CHOICE,
            options=["Docker 容器化部署", "本地直接运行", "两者都需要"],
            default="Docker 容器化部署",
            required=True,
        )

        # 从解析结果中添加澄清问题
        for q in req.clarification_questions:
            self.manager.add_question(
                question=q.get("question", str(q)),
                type=QuestionType.TEXT,
                required=False,
            )

    def get_current_question(self) -> Optional[dict]:
        """
        获取当前待回答的问题

        Returns:
            dict: 问题信息，或 None 如果没有问题
        """
        question = self.manager.get_next_question()
        if not question:
            return None

        return {
            "id": question.id,
            "question": question.question,
            "type": question.type.value,
            "options": question.options,
            "default": question.default,
        }

    def answer(self, answer: any) -> dict:
        """
        回答当前问题

        Args:
            answer: 用户答案

        Returns:
            dict: 回答结果和下一个问题
        """
        question = self.manager.get_next_question()
        if not question:
            return {
                "success": False,
                "error": "没有待回答的问题",
                "state": self.manager.state.value,
            }

        # 记录回答
        self.manager.answer_question(question.id, answer)

        # 根据问题类型处理答案
        self._process_answer(question, answer)

        # 记录对话轮次
        self.manager.add_turn(
            user_input=str(answer),
            system_response=f"已记录回答: {question.question[:30]}..."
        )

        # 检查是否还有问题
        next_question = self.get_current_question()

        if next_question is None:
            # 所有问题已回答，可以进入批准阶段
            self.manager.transition_state(DialogState.REFINING)
            return {
                "success": True,
                "state": "refining",
                "message": "所有确认问题已完成",
                "next_action": "approve_or_modify",
                "summary": self.manager.get_requirement(),
            }

        return {
            "success": True,
            "state": "confirming",
            "next_question": next_question,
        }

    def _process_answer(self, question: Question, answer: any):
        """处理用户答案，更新需求数据"""
        if "项目类型" in question.question:
            if answer is False:
                # 用户表示项目类型不正确，需要更正
                pass  # 可以添加更多逻辑让用户选择正确类型

        elif "技术栈" in question.question:
            if answer is False:
                self.manager.update_requirement(
                    "tech_stack_confirmed",
                    False,
                    "用户不接受建议的技术栈"
                )

        elif "功能" in question.question:
            if answer is False:
                self.manager.update_requirement(
                    "all_features_required",
                    False,
                    "用户不需要实现所有功能"
                )

        elif "数据库" in question.question:
            db_mapping = {
                "SQLite (轻量级)": "sqlite",
                "PostgreSQL (生产级)": "postgresql",
                "MongoDB (文档型)": "mongodb",
                "MySQL (传统)": "mysql",
            }
            db_type = db_mapping.get(answer, "sqlite")
            self.manager.update_requirement(
                "database_type",
                db_type,
                f"用户选择数据库: {answer}"
            )

        elif "部署" in question.question:
            deploy_mapping = {
                "Docker 容器化部署": "docker",
                "本地直接运行": "local",
                "两者都需要": "both",
            }
            deploy_type = deploy_mapping.get(answer, "docker")
            self.manager.update_requirement(
                "deployment_type",
                deploy_type,
                f"用户选择部署方式: {answer}"
            )

    def approve(self) -> dict:
        """
        批准当前需求

        Returns:
            dict: 批准结果
        """
        # 检查未回答问题
        unanswered = self.manager.get_unanswered_questions()
        if unanswered:
            return {
                "success": False,
                "error": f"还有 {len(unanswered)} 个问题未回答",
                "unanswered_questions": [q.question for q in unanswered],
            }

        if self.manager.approve():
            self.manager.add_turn(
                user_input="批准",
                system_response="需求已确认，准备生成代码"
            )
            return {
                "success": True,
                "state": "approved",
                "requirement": self.manager.get_requirement(),
                "change_history": self.manager.get_change_history(),
                "dialog_summary": self.manager.get_dialog_summary(),
            }

        return {
            "success": False,
            "error": "批准失败",
        }

    def modify(self, field: str, new_value: any, reason: str = "") -> dict:
        """
        修改需求字段

        Args:
            field: 字段名
            new_value: 新值
            reason: 修改原因

        Returns:
            dict: 修改结果
        """
        self.manager.update_requirement(field, new_value, reason)
        self.manager.add_turn(
            user_input=f"修改 {field} 为 {new_value}",
            system_response=f"已更新: {field}"
        )

        return {
            "success": True,
            "state": "refining",
            "message": f"已更新 {field}",
            "requirement": self.manager.get_requirement(),
        }

    def cancel(self, reason: str = "") -> dict:
        """
        取消流程

        Args:
            reason: 取消原因

        Returns:
            dict: 取消结果
        """
        self.manager.cancel(reason)
        return {
            "success": True,
            "state": "cancelled",
            "reason": reason,
        }

    def get_status(self) -> dict:
        """获取当前流程状态"""
        return {
            "state": self.manager.state.value,
            "requirement": self.manager.get_requirement(),
            "dialog_summary": self.manager.get_dialog_summary(),
            "unanswered_count": len(self.manager.get_unanswered_questions()),
            "changes_count": len(self.manager.get_change_history()),
        }

    def get_final_requirement(self) -> Optional[dict]:
        """
        获取最终确认的需求

        Returns:
            dict: 最终需求，如果未批准则返回 None
        """
        if not self.manager.is_approved:
            return None

        return self.manager.get_requirement()
