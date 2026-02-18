"""Tests for Coder-Factory core module"""
import pytest
from coder_factory import __version__
from coder_factory.core.factory import CoderFactory, ProcessResult
from coder_factory.core.state import StateManager


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


def test_coder_factory_init():
    """测试 CoderFactory 初始化"""
    factory = CoderFactory(output_dir="./test_workspace")
    assert factory.output_dir.name == "test_workspace"


def test_coder_factory_process_requirement():
    """测试需求处理"""
    factory = CoderFactory()
    result = factory.process_requirement("创建一个简单的 REST API")
    assert result.success is True
