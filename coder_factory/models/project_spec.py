"""
项目规格数据模型
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Runtime(Enum):
    """运行时环境"""
    PYTHON = "python"
    NODEJS = "nodejs"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    MIXED = "mixed"


class FrontendFramework(Enum):
    """前端框架"""
    REACT = "react"
    VUE = "vue"
    SVELTE = "svelte"
    NEXTJS = "nextjs"
    NUXT = "nuxt"
    NONE = "none"


class BackendFramework(Enum):
    """后端框架"""
    FASTAPI = "fastapi"
    DJANGO = "django"
    FLASK = "flask"
    EXPRESS = "express"
    NESTJS = "nestjs"
    GO_GIN = "gin"
    NONE = "none"


class DatabaseType(Enum):
    """数据库类型"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    SQLITE = "sqlite"
    REDIS = "redis"
    NONE = "none"


@dataclass
class TechStack:
    """技术栈配置"""
    runtime: Runtime = Runtime.PYTHON
    runtime_version: str = "3.11"
    frontend: FrontendFramework = FrontendFramework.NONE
    backend: BackendFramework = BackendFramework.FASTAPI
    database: DatabaseType = DatabaseType.SQLITE
    additional_packages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "runtime": self.runtime.value,
            "runtime_version": self.runtime_version,
            "frontend": self.frontend.value,
            "backend": self.backend.value,
            "database": self.database.value,
            "additional_packages": self.additional_packages,
        }


@dataclass
class ProjectSpec:
    """
    项目规格

    定义项目的完整技术规格
    """
    name: str = ""
    description: str = ""
    tech_stack: TechStack = field(default_factory=TechStack)
    directories: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    environment_vars: dict[str, str] = field(default_factory=dict)
    docker_enabled: bool = True
    github_repo: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "tech_stack": self.tech_stack.to_dict(),
            "directories": self.directories,
            "entry_points": self.entry_points,
            "environment_vars": self.environment_vars,
            "docker_enabled": self.docker_enabled,
            "github_repo": self.github_repo,
        }
