"""
交互确认系统 (F002)

管理用户与 Coder-Factory 的多轮对话
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Any
from datetime import datetime
import uuid


def _get_timestamp() -> datetime:
    """获取当前时间戳"""
    return datetime.now()


class DialogState(Enum):
    """对话状态"""
    IDLE = "idle"                    # 空闲，等待输入
    PARSING = "parsing"              # 正在解析需求
    CONFIRMING = "confirming"        # 确认需求
    CLARIFYING = "clarifying"        # 澄清问题
    REFINING = "refining"            # 优化需求
    APPROVED = "approved"            # 已批准
    CANCELLED = "cancelled"          # 已取消


class QuestionType(Enum):
    """问题类型"""
    CONFIRM = "confirm"              # 是/否确认
    CHOICE = "choice"                # 多选一
    MULTI_SELECT = "multi_select"    # 多选
    TEXT = "text"                    # 文本输入
    NUMBER = "number"                # 数字输入


@dataclass
class Question:
    """交互问题"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    question: str = ""
    type: QuestionType = QuestionType.CONFIRM
    options: list[str] = field(default_factory=list)
    default: Any = None
    answer: Any = None
    answered: bool = False
    required: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.question,
            "type": self.type.value,
            "options": self.options,
            "default": self.default,
            "answer": self.answer,
            "answered": self.answered,
            "required": self.required,
        }


@dataclass
class DialogTurn:
    """对话轮次"""
    turn_id: int
    user_input: str
    system_response: str
    state_before: DialogState
    state_after: DialogState
    timestamp: datetime = field(default_factory=_get_timestamp)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "turn_id": self.turn_id,
            "user_input": self.user_input,
            "system_response": self.system_response,
            "state_before": self.state_before.value,
            "state_after": self.state_after.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ChangeRecord:
    """需求变更记录"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    field_name: str = ""             # 变更的字段
    old_value: Any = None
    new_value: Any = None
    reason: str = ""                 # 变更原因
    timestamp: datetime = field(default_factory=_get_timestamp)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "field": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }


class DialogStateMachine:
    """
    对话状态机

    管理对话的状态转换：
    IDLE -> PARSING -> CONFIRMING -> CLARIFYING -> REFINING -> APPROVED
                        |                               |
                        +----------- CANCELLED <--------+
    """

    # 有效状态转换
    TRANSITIONS = {
        DialogState.IDLE: [DialogState.PARSING],
        DialogState.PARSING: [DialogState.CONFIRMING, DialogState.CLARIFYING, DialogState.CANCELLED],
        DialogState.CONFIRMING: [DialogState.CLARIFYING, DialogState.REFINING, DialogState.APPROVED, DialogState.CANCELLED],
        DialogState.CLARIFYING: [DialogState.CONFIRMING, DialogState.REFINING, DialogState.APPROVED, DialogState.CANCELLED],
        DialogState.REFINING: [DialogState.CONFIRMING, DialogState.CLARIFYING, DialogState.APPROVED, DialogState.CANCELLED],
        DialogState.APPROVED: [DialogState.IDLE],
        DialogState.CANCELLED: [DialogState.IDLE],
    }

    def __init__(self):
        self._state = DialogState.IDLE
        self._history: list[DialogState] = [DialogState.IDLE]

    @property
    def state(self) -> DialogState:
        """当前状态"""
        return self._state

    def can_transition_to(self, new_state: DialogState) -> bool:
        """检查是否可以转换到目标状态"""
        return new_state in self.TRANSITIONS.get(self._state, [])

    def transition(self, new_state: DialogState) -> bool:
        """
        执行状态转换

        Returns:
            bool: 转换是否成功
        """
        if not self.can_transition_to(new_state):
            return False

        self._history.append(new_state)
        self._state = new_state
        return True

    def reset(self):
        """重置状态机"""
        self._state = DialogState.IDLE
        self._history = [DialogState.IDLE]

    def get_history(self) -> list[DialogState]:
        """获取状态历史"""
        return self._history.copy()


class InteractionManager:
    """
    交互管理器

    核心功能：
    1. 管理多轮对话
    2. 追踪需求变更
    3. 生成确认问题
    """

    def __init__(self):
        self.state_machine = DialogStateMachine()
        self._turns: list[DialogTurn] = []
        self._questions: list[Question] = []
        self._changes: list[ChangeRecord] = []
        self._current_turn_id = 0
        self._requirement_data: dict = {}

    @property
    def state(self) -> DialogState:
        """当前对话状态"""
        return self.state_machine.state

    @property
    def is_approved(self) -> bool:
        """需求是否已批准"""
        return self.state == DialogState.APPROVED

    @property
    def is_cancelled(self) -> bool:
        """对话是否已取消"""
        return self.state == DialogState.CANCELLED

    def start_dialog(self, initial_requirement: dict) -> DialogState:
        """
        开始新对话

        Args:
            initial_requirement: 初始需求数据

        Returns:
            DialogState: 新状态
        """
        self._reset()
        self._requirement_data = initial_requirement.copy()

        if self.state_machine.transition(DialogState.PARSING):
            return self.state

        return self.state

    def add_turn(
        self,
        user_input: str,
        system_response: str,
        metadata: dict | None = None
    ) -> DialogTurn:
        """
        添加对话轮次

        Args:
            user_input: 用户输入
            system_response: 系统响应
            metadata: 额外元数据

        Returns:
            DialogTurn: 新增的对话轮次
        """
        self._current_turn_id += 1
        turn = DialogTurn(
            turn_id=self._current_turn_id,
            user_input=user_input,
            system_response=system_response,
            state_before=self.state,
            state_after=self.state,
            metadata=metadata or {}
        )
        self._turns.append(turn)
        return turn

    def transition_state(self, new_state: DialogState) -> bool:
        """
        转换对话状态

        Args:
            new_state: 目标状态

        Returns:
            bool: 是否成功
        """
        old_state = self.state
        if self.state_machine.transition(new_state):
            # 更新最后一个轮次的状态
            if self._turns:
                self._turns[-1].state_after = new_state
            return True
        return False

    def add_question(
        self,
        question: str,
        type: QuestionType = QuestionType.CONFIRM,
        options: list[str] | None = None,
        default: Any = None,
        required: bool = True
    ) -> Question:
        """
        添加需要用户确认的问题

        Args:
            question: 问题文本
            type: 问题类型
            options: 选项列表 (用于 CHOICE 和 MULTI_SELECT)
            default: 默认值
            required: 是否必须回答

        Returns:
            Question: 新增的问题对象
        """
        q = Question(
            question=question,
            type=type,
            options=options or [],
            default=default,
            required=required,
        )
        self._questions.append(q)
        return q

    def answer_question(self, question_id: str, answer: Any) -> bool:
        """
        回答问题

        Args:
            question_id: 问题ID
            answer: 答案

        Returns:
            bool: 是否成功
        """
        for q in self._questions:
            if q.id == question_id:
                q.answer = answer
                q.answered = True
                return True
        return False

    def get_unanswered_questions(self) -> list[Question]:
        """获取未回答的问题"""
        return [q for q in self._questions if not q.answered and q.required]

    def get_next_question(self) -> Question | None:
        """获取下一个未回答的问题"""
        unanswered = self.get_unanswered_questions()
        return unanswered[0] if unanswered else None

    def record_change(
        self,
        field: str,
        old_value: Any,
        new_value: Any,
        reason: str = ""
    ) -> ChangeRecord:
        """
        记录需求变更

        Args:
            field: 变更的字段名
            old_value: 旧值
            new_value: 新值
            reason: 变更原因

        Returns:
            ChangeRecord: 变更记录
        """
        change = ChangeRecord(
            field_name=field,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
        )
        self._changes.append(change)
        return change

    def update_requirement(self, field: str, value: Any, reason: str = "") -> bool:
        """
        更新需求数据

        Args:
            field: 字段名 (支持点号路径，如 "tech_stack.runtime")
            value: 新值
            reason: 变更原因

        Returns:
            bool: 是否成功
        """
        old_value = self._get_nested_value(field)
        self._set_nested_value(field, value)
        self.record_change(field, old_value, value, reason)
        return True

    def _get_nested_value(self, path: str) -> Any:
        """获取嵌套字段值"""
        keys = path.split(".")
        value = self._requirement_data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    def _set_nested_value(self, path: str, value: Any):
        """设置嵌套字段值"""
        keys = path.split(".")
        data = self._requirement_data
        for key in keys[:-1]:
            if key not in data:
                data[key] = {}
            data = data[key]
        data[keys[-1]] = value

    def get_requirement(self) -> dict:
        """获取当前需求数据"""
        return self._requirement_data.copy()

    def get_dialog_summary(self) -> dict:
        """获取对话摘要"""
        return {
            "state": self.state.value,
            "total_turns": len(self._turns),
            "total_questions": len(self._questions),
            "answered_questions": len([q for q in self._questions if q.answered]),
            "total_changes": len(self._changes),
            "is_approved": self.is_approved,
            "is_cancelled": self.is_cancelled,
        }

    def get_change_history(self) -> list[dict]:
        """获取变更历史"""
        return [c.to_dict() for c in self._changes]

    def get_dialog_history(self) -> list[dict]:
        """获取对话历史"""
        return [t.to_dict() for t in self._turns]

    def approve(self) -> bool:
        """批准当前需求"""
        # 检查是否还有未回答的必须问题
        unanswered = self.get_unanswered_questions()
        if unanswered:
            return False

        return self.transition_state(DialogState.APPROVED)

    def cancel(self, reason: str = "") -> bool:
        """取消对话"""
        if reason:
            self.add_turn("", f"对话已取消: {reason}")
        return self.transition_state(DialogState.CANCELLED)

    def _reset(self):
        """重置管理器"""
        self.state_machine.reset()
        self._turns = []
        self._questions = []
        self._changes = []
        self._current_turn_id = 0
        self._requirement_data = {}

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "state": self.state.value,
            "requirement": self._requirement_data,
            "turns": self.get_dialog_history(),
            "questions": [q.to_dict() for q in self._questions],
            "changes": self.get_change_history(),
            "summary": self.get_dialog_summary(),
        }
