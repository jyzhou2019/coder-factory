"""
Coder-Factory: AI自主代码工厂
从需求到交付的全自动化生产线
"""

__version__ = "0.1.0"
__author__ = "jyzhou2019"

from .core.factory import CoderFactory
from .core.state import StateManager

__all__ = ["CoderFactory", "StateManager"]
