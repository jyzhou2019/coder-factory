"""Tests for Coder-Factory core module"""
import pytest
from pathlib import Path

from coder_factory import __version__
from coder_factory.core.factory import CoderFactory, ProcessResult
from coder_factory.core.state import StateManager
from coder_factory.models.requirement import (
    Requirement, TaskNode, TaskType, TaskPriority, TaskStatus
)
from coder_factory.models.project_spec import TechStack, Runtime
from coder_factory.engines.requirement_parser import RequirementParser, ParseResult
from coder_factory.engines.interaction_manager import (
    InteractionManager,
    DialogState,
    QuestionType,
    Question,
    DialogStateMachine,
)
from coder_factory.engines.confirmation_flow import ConfirmationFlow


def test_version():
    """测试版本号"""
    assert __version__ == "0.1.0"


def test_process_result_dataclass():
    """测试 ProcessResult 数据类"""
    result = ProcessResult(
        success=True,
        message="Test message"
    )
    assert result.success is True
    assert result.error is None
    assert result.requirement is None


def test_coder_factory_init():
    """测试 CoderFactory 初始化"""
    factory = CoderFactory(output_dir="./test_workspace")
    assert factory.output_dir.name == "test_workspace"
    assert factory.parser is not None
    assert factory.claude is not None


def test_task_node():
    """测试 TaskNode"""
    task = TaskNode(
        title="测试任务",
        description="这是一个测试任务",
        task_type=TaskType.BACKEND,
        priority=TaskPriority.HIGH,
    )

    assert task.title == "测试任务"
    assert task.task_type == TaskType.BACKEND
    assert task.status == TaskStatus.PENDING

    # 测试添加子任务
    subtask = TaskNode(title="子任务")
    task.add_subtask(subtask)
    assert len(task.subtasks) == 1

    # 测试展平
    flat = task.flatten()
    assert len(flat) == 2


def test_task_node_to_dict():
    """测试 TaskNode 序列化"""
    task = TaskNode(
        title="API 开发",
        task_type=TaskType.API,
        priority=TaskPriority.P0,
    )
    data = task.to_dict()

    assert data["title"] == "API 开发"
    assert data["type"] == "api"
    assert data["priority"] == "P0"


def test_requirement():
    """测试 Requirement"""
    req = Requirement(
        raw_text="创建一个 REST API",
        summary="REST API 项目",
        project_type="api",
        features=["用户认证", "数据管理"],
    )

    assert req.project_type == "api"
    assert len(req.features) == 2

    # 测试序列化
    data = req.to_dict()
    assert data["raw_text"] == "创建一个 REST API"
    assert "created_at" in data


def test_requirement_with_tasks():
    """测试带任务树的 Requirement"""
    req = Requirement(
        raw_text="测试需求",
        task_tree=TaskNode(
            title="根任务",
            subtasks=[
                TaskNode(title="任务1"),
                TaskNode(title="任务2", subtasks=[
                    TaskNode(title="子任务2.1")
                ]),
            ]
        )
    )

    all_tasks = req.get_all_tasks()
    assert len(all_tasks) == 4  # 根 + 任务1 + 任务2 + 子任务2.1


def test_tech_stack():
    """测试 TechStack"""
    stack = TechStack(
        runtime=Runtime.PYTHON,
        runtime_version="3.11",
    )

    data = stack.to_dict()
    assert data["runtime"] == "python"
    assert data["runtime_version"] == "3.11"


def test_state_manager():
    """测试 StateManager"""
    manager = StateManager(base_dir=Path("."))

    # 测试加载 features
    data = manager.load_features()
    assert "features" in data

    # 测试获取下一个待处理功能
    feature = manager.get_next_pending_feature()
    assert feature is not None
    assert feature["status"] == "pending" or feature["status"] == "in_progress"


def test_requirement_parser_init():
    """测试 RequirementParser 初始化"""
    parser = RequirementParser(workspace="./workspace")
    assert parser.client is not None


def test_complexity_estimation():
    """测试复杂度估算"""
    parser = RequirementParser()

    # 简单任务
    simple = parser._estimate_complexity({
        "title": "简单任务",
        "description": "短描述",
        "subtasks": []
    })
    assert simple == 1

    # 复杂任务
    complex_task = parser._estimate_complexity({
        "title": "复杂任务",
        "description": "这是一个非常长的描述" * 50,
        "subtasks": ["子1", "子2", "子3", "子4", "子5", "子6"]
    })
    assert complex_task >= 3


# ===== F002 交互确认系统测试 =====

def test_dialog_state_machine():
    """测试对话状态机"""
    sm = DialogStateMachine()

    assert sm.state == DialogState.IDLE

    # 测试有效转换
    assert sm.can_transition_to(DialogState.PARSING)
    assert sm.transition(DialogState.PARSING)
    assert sm.state == DialogState.PARSING

    # 测试无效转换
    assert not sm.can_transition_to(DialogState.IDLE)

    # 测试历史记录
    history = sm.get_history()
    assert len(history) == 2


def test_dialog_state_machine_reset():
    """测试状态机重置"""
    sm = DialogStateMachine()
    sm.transition(DialogState.PARSING)
    sm.transition(DialogState.CONFIRMING)

    sm.reset()

    assert sm.state == DialogState.IDLE
    assert len(sm.get_history()) == 1


def test_question():
    """测试问题对象"""
    q = Question(
        question="是否确认?",
        type=QuestionType.CONFIRM,
        default=True,
    )

    assert q.question == "是否确认?"
    assert q.type == QuestionType.CONFIRM
    assert q.answered is False

    # 测试序列化
    data = q.to_dict()
    assert data["type"] == "confirm"


def test_interaction_manager():
    """测试交互管理器"""
    manager = InteractionManager()

    assert manager.state == DialogState.IDLE

    # 启动对话
    initial_data = {"summary": "测试需求"}
    manager.start_dialog(initial_data)

    # 添加问题
    q = manager.add_question("项目类型正确吗?", QuestionType.CONFIRM)
    assert len(manager.get_unanswered_questions()) == 1

    # 回答问题
    manager.answer_question(q.id, True)
    assert len(manager.get_unanswered_questions()) == 0


def test_interaction_manager_changes():
    """测试需求变更追踪"""
    manager = InteractionManager()
    manager.start_dialog({"feature": "original"})

    # 记录变更
    manager.update_requirement("feature", "modified", "用户修改")
    changes = manager.get_change_history()

    assert len(changes) == 1
    assert changes[0]["old_value"] == "original"
    assert changes[0]["new_value"] == "modified"


def test_interaction_manager_approve():
    """测试批准流程"""
    manager = InteractionManager()
    manager.start_dialog({"summary": "test"})

    # 添加非必须问题
    manager.add_question("可选问题", QuestionType.TEXT, required=False)

    # 直接批准
    assert manager.approve()
    assert manager.is_approved


def test_interaction_manager_cancel():
    """测试取消流程"""
    manager = InteractionManager()
    manager.start_dialog({"summary": "test"})
    manager.transition_state(DialogState.CONFIRMING)

    manager.cancel("测试取消")

    assert manager.is_cancelled


def test_confirmation_flow_init():
    """测试确认流程初始化"""
    flow = ConfirmationFlow()

    assert flow.manager is not None
    assert flow.parser is not None


def test_interaction_manager_dialog_turns():
    """测试对话轮次"""
    manager = InteractionManager()
    manager.start_dialog({})

    # 添加对话轮次
    turn = manager.add_turn(
        user_input="我想修改需求",
        system_response="好的，请告诉我您想修改什么"
    )

    assert turn.turn_id == 1
    assert turn.user_input == "我想修改需求"

    history = manager.get_dialog_history()
    assert len(history) == 1


def test_interaction_manager_nested_update():
    """测试嵌套字段更新"""
    manager = InteractionManager()
    manager.start_dialog({
        "tech_stack": {
            "runtime": "python"
        }
    })

    manager.update_requirement("tech_stack.runtime", "nodejs", "用户选择")

    req = manager.get_requirement()
    assert req["tech_stack"]["runtime"] == "nodejs"

