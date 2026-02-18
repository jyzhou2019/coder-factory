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
