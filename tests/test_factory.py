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


# ===== F003 架构设计引擎测试 =====

def test_tech_stack_knowledge_base():
    """测试技术栈知识库"""
    from coder_factory.engines.tech_stack_kb import (
        TechStackKnowledgeBase, ProjectCategory, ScaleLevel
    )

    kb = TechStackKnowledgeBase()

    # 测试获取技术选项
    python_opt = kb.get_option("python")
    assert python_opt is not None
    assert python_opt.name == "Python"

    # 测试按类型获取模板
    web_templates = kb.get_templates_by_category(ProjectCategory.WEB_APP)
    assert len(web_templates) > 0

    # 测试推荐
    recommendations = kb.recommend_for_project(ProjectCategory.API_SERVICE)
    assert len(recommendations) > 0


def test_tech_option():
    """测试技术选项"""
    from coder_factory.engines.tech_stack_kb import TechOption

    opt = TechOption(
        name="TestTech",
        category="runtime",
        pros=["fast", "simple"],
        cons=["new"],
        best_for=["api", "microservice"],
        complexity=2,
        popularity=4,
        performance=4,
    )

    assert opt.name == "TestTech"
    assert len(opt.pros) == 2
    assert opt.complexity == 2


def test_tech_comparison():
    """测试技术比较"""
    from coder_factory.engines.tech_stack_kb import TechStackKnowledgeBase

    kb = TechStackKnowledgeBase()
    comparison = kb.compare_techs(["python", "nodejs"])

    assert "python" in comparison
    assert "nodejs" in comparison
    assert comparison["python"]["complexity"] == 1
    assert comparison["nodejs"]["complexity"] == 2


def test_architecture_designer_init():
    """测试架构设计器初始化"""
    from coder_factory.engines.architecture_designer import ArchitectureDesigner

    designer = ArchitectureDesigner(workspace="./test_workspace")
    assert designer.kb is not None
    assert designer.claude is not None


def test_architecture_component():
    """测试架构组件"""
    from coder_factory.engines.architecture_designer import ArchitectureComponent

    comp = ArchitectureComponent(
        name="API Server",
        type="backend",
        technology="FastAPI",
        description="Main API service",
        connections=["Database"],
    )

    assert comp.name == "API Server"
    assert comp.technology == "FastAPI"
    assert "Database" in comp.connections

    # 测试序列化
    data = comp.to_dict()
    assert data["name"] == "API Server"
    assert data["type"] == "backend"


def test_architecture_design():
    """测试架构设计结果"""
    from coder_factory.engines.architecture_designer import (
        ArchitectureDesign, ArchitectureComponent
    )

    design = ArchitectureDesign(
        project_name="test_project",
        description="Test project description",
        components=[
            ArchitectureComponent(name="API", type="backend", technology="FastAPI")
        ],
        tech_stack={"runtime": "python", "backend": "fastapi"},
        directory_structure={"src": {}, "tests": {}},
    )

    assert design.project_name == "test_project"
    assert len(design.components) == 1

    # 测试序列化
    data = design.to_dict()
    assert data["project_name"] == "test_project"
    assert "created_at" in data


def test_determine_category():
    """测试项目类型判断"""
    from coder_factory.engines.architecture_designer import ArchitectureDesigner
    from coder_factory.models.requirement import Requirement

    designer = ArchitectureDesigner()

    # 测试不同项目类型
    req_api = Requirement(project_type="api", summary="API service")
    category = designer._determine_category(req_api)
    assert category.value == "api_service"

    req_cli = Requirement(project_type="cli", summary="CLI tool")
    category = designer._determine_category(req_cli)
    assert category.value == "cli_tool"


def test_estimate_scale():
    """测试规模估算"""
    from coder_factory.engines.architecture_designer import ArchitectureDesigner
    from coder_factory.models.requirement import Requirement, TaskNode

    designer = ArchitectureDesigner()

    # 小项目
    req_small = Requirement(summary="Small project")
    scale = designer._estimate_scale(req_small)
    assert scale.value == "small"

    # 大项目 (带任务树)
    req_large = Requirement(
        summary="Large project",
        task_tree=TaskNode(
            title="Root",
            subtasks=[
                TaskNode(title=f"Task {i}", estimated_complexity=3)
                for i in range(15)
            ]
        )
    )
    scale = designer._estimate_scale(req_large)
    assert scale.value in ["medium", "large"]


def test_generate_architecture_document():
    """测试架构文档生成"""
    from coder_factory.engines.architecture_designer import (
        ArchitectureDesigner, ArchitectureDesign, ArchitectureComponent
    )

    designer = ArchitectureDesigner()

    design = ArchitectureDesign(
        project_name="my_api",
        description="My API project",
        components=[
            ArchitectureComponent(
                name="API",
                type="backend",
                technology="FastAPI",
                description="REST API"
            )
        ],
        tech_stack={"runtime": "python"},
        directory_structure={"src": {}, "tests": {}},
        recommendations=["Use caching"],
    )

    doc = designer.generate_architecture_document(design)

    assert "# my_api" in doc
    assert "My API project" in doc
    assert "FastAPI" in doc
    assert "Use caching" in doc

