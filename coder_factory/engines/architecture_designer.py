"""
架构设计引擎 (F003)

使用 Claude Code 和技术栈知识库设计系统架构
"""

import json
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from datetime import datetime

from .tech_stack_kb import (
    TechStackKnowledgeBase,
    ProjectCategory,
    ScaleLevel,
    TechStackTemplate,
)
from .claude_client import ClaudeCodeClient
from ..models.requirement import Requirement


@dataclass
class ArchitectureComponent:
    """架构组件"""
    name: str
    type: str              # frontend/backend/database/cache/etc
    technology: str
    description: str = ""
    connections: list[str] = field(default_factory=list)
    config: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "technology": self.technology,
            "description": self.description,
            "connections": self.connections,
            "config": self.config,
        }


@dataclass
class ArchitectureDesign:
    """架构设计结果"""
    project_name: str
    description: str
    components: list[ArchitectureComponent]
    tech_stack: dict
    directory_structure: dict
    api_endpoints: list[dict] = field(default_factory=list)
    data_models: list[dict] = field(default_factory=list)
    deployment: dict = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "description": self.description,
            "components": [c.to_dict() for c in self.components],
            "tech_stack": self.tech_stack,
            "directory_structure": self.directory_structure,
            "api_endpoints": self.api_endpoints,
            "data_models": self.data_models,
            "deployment": self.deployment,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat(),
        }


class ArchitectureDesigner:
    """
    架构设计器

    核心功能：
    1. 分析需求，确定项目类型
    2. 推荐技术栈
    3. 设计系统架构
    4. 生成目录结构
    5. 规划 API 和数据模型
    """

    def __init__(self, workspace: Path | str = "./workspace"):
        self.workspace = Path(workspace)
        self.kb = TechStackKnowledgeBase()
        self.claude = ClaudeCodeClient(workspace)

    def analyze_and_design(
        self,
        requirement: Requirement,
        preferences: dict | None = None
    ) -> ArchitectureDesign:
        """
        分析需求并设计架构

        Args:
            requirement: 需求对象
            preferences: 用户偏好

        Returns:
            ArchitectureDesign: 架构设计结果
        """
        # 1. 确定项目类型
        category = self._determine_category(requirement)

        # 2. 估算项目规模
        scale = self._estimate_scale(requirement)

        # 3. 推荐技术栈
        templates = self.kb.recommend_for_project(category, scale, preferences)
        selected_template = templates[0] if templates else None

        # 4. 使用 Claude Code 深度设计
        design_prompt = self._build_design_prompt(requirement, selected_template)
        claude_result = self.claude.parse_requirement(design_prompt)

        # 5. 构建架构设计
        design = self._build_architecture(
            requirement,
            selected_template,
            claude_result,
            preferences
        )

        return design

    def _determine_category(self, requirement: Requirement) -> ProjectCategory:
        """确定项目类型"""
        project_type = requirement.project_type.lower()

        mapping = {
            "web": ProjectCategory.WEB_APP,
            "web_app": ProjectCategory.WEB_APP,
            "api": ProjectCategory.API_SERVICE,
            "rest_api": ProjectCategory.API_SERVICE,
            "cli": ProjectCategory.CLI_TOOL,
            "command_line": ProjectCategory.CLI_TOOL,
            "desktop": ProjectCategory.DESKTOP_APP,
            "mobile": ProjectCategory.MOBILE_APP,
            "library": ProjectCategory.LIBRARY,
            "package": ProjectCategory.LIBRARY,
            "microservice": ProjectCategory.MICROSERVICE,
            "static": ProjectCategory.STATIC_SITE,
            "realtime": ProjectCategory.REALTIME_APP,
        }

        return mapping.get(project_type, ProjectCategory.WEB_APP)

    def _estimate_scale(self, requirement: Requirement) -> ScaleLevel:
        """估算项目规模"""
        if not requirement.task_tree:
            return ScaleLevel.SMALL

        total_complexity = requirement.task_tree.get_total_complexity()
        task_count = len(requirement.get_all_tasks())

        # 综合评估
        score = total_complexity + task_count

        if score < 10:
            return ScaleLevel.SMALL
        elif score < 30:
            return ScaleLevel.MEDIUM
        else:
            return ScaleLevel.LARGE

    def _build_design_prompt(
        self,
        requirement: Requirement,
        template: Optional[TechStackTemplate]
    ) -> str:
        """构建设计提示词"""
        template_info = ""
        if template:
            template_info = f"""
推荐技术栈模板: {template.name}
- 运行时: {template.runtime}
- 前端: {template.frontend or '无'}
- 后端: {template.backend or '无'}
- 数据库: {template.database or '无'}
- 描述: {template.description}
"""

        return f"""请为以下项目设计系统架构，并以 JSON 格式输出。

## 项目需求
摘要: {requirement.summary}
类型: {requirement.project_type}
核心功能: {json.dumps(requirement.features, ensure_ascii=False)}
约束条件: {json.dumps(requirement.constraints, ensure_ascii=False)}

{template_info}

## 请输出以下 JSON 结构:
{{
    "project_name": "项目名称（英文，小写，下划线分隔）",
    "description": "项目描述",
    "components": [
        {{
            "name": "组件名称",
            "type": "frontend/backend/database/cache/api/etc",
            "technology": "使用的技术",
            "description": "组件描述",
            "connections": ["连接的其他组件"]
        }}
    ],
    "tech_stack": {{
        "runtime": "运行时",
        "frontend": "前端框架或 null",
        "backend": "后端框架或 null",
        "database": "数据库或 null",
        "additional": ["额外的包"]
    }},
    "directory_structure": {{
        "src": {{}},
        "tests": {{}},
        "docs": {{}}
    }},
    "api_endpoints": [
        {{
            "path": "/api/path",
            "method": "GET/POST/etc",
            "description": "描述"
        }}
    ],
    "data_models": [
        {{
            "name": "模型名",
            "fields": [
                {{"name": "字段名", "type": "类型", "required": true}}
            ]
        }}
    ],
    "deployment": {{
        "docker": true,
        "environment_vars": ["需要的环境变量"],
        "ports": [8080]
    }},
    "recommendations": ["架构建议"]
}}"""

    def _build_architecture(
        self,
        requirement: Requirement,
        template: Optional[TechStackTemplate],
        claude_result: dict,
        preferences: dict | None = None
    ) -> ArchitectureDesign:
        """构建架构设计"""
        # 从 Claude 结果提取数据
        data = claude_result if "error" not in claude_result else {}

        # 如果 Claude 结果有效，使用它
        if "project_name" in data:
            components = [
                ArchitectureComponent(
                    name=c.get("name", ""),
                    type=c.get("type", ""),
                    technology=c.get("technology", ""),
                    description=c.get("description", ""),
                    connections=c.get("connections", []),
                    config=c.get("config", {}),
                )
                for c in data.get("components", [])
            ]

            return ArchitectureDesign(
                project_name=data.get("project_name", "project"),
                description=data.get("description", requirement.summary),
                components=components,
                tech_stack=data.get("tech_stack", {}),
                directory_structure=data.get("directory_structure", {}),
                api_endpoints=data.get("api_endpoints", []),
                data_models=data.get("data_models", []),
                deployment=data.get("deployment", {}),
                recommendations=data.get("recommendations", []),
            )

        # 否则使用模板构建基础架构
        return self._build_from_template(requirement, template)

    def _build_from_template(
        self,
        requirement: Requirement,
        template: Optional[TechStackTemplate]
    ) -> ArchitectureDesign:
        """从模板构建架构"""
        components = []

        # 后端组件
        if template and template.backend:
            components.append(ArchitectureComponent(
                name="API Server",
                type="backend",
                technology=template.backend,
                description="主 API 服务",
                connections=["Database"] if template.database else [],
            ))

        # 前端组件
        if template and template.frontend:
            components.append(ArchitectureComponent(
                name="Frontend",
                type="frontend",
                technology=template.frontend,
                description="用户界面",
                connections=["API Server"],
            ))

        # 数据库组件
        if template and template.database:
            components.append(ArchitectureComponent(
                name="Database",
                type="database",
                technology=template.database,
                description="数据存储",
                connections=[],
            ))

        # 构建目录结构
        dir_structure = self._generate_directory_structure(template)

        # 构建技术栈
        tech_stack = {}
        if template:
            tech_stack = {
                "runtime": template.runtime,
                "frontend": template.frontend,
                "backend": template.backend,
                "database": template.database,
                "additional": template.additional,
            }

        return ArchitectureDesign(
            project_name=requirement.project_type.replace(" ", "_").lower(),
            description=requirement.summary,
            components=components,
            tech_stack=tech_stack,
            directory_structure=dir_structure,
            deployment={"docker": True},
            recommendations=["建议使用 Docker 进行部署"],
        )

    def _generate_directory_structure(self, template: Optional[TechStackTemplate]) -> dict:
        """生成目录结构"""
        if not template:
            return {"src": {}, "tests": {}, "docs": {}}

        if template.runtime == "python":
            return {
                "src": {
                    f"{template.project_name if hasattr(template, 'project_name') else 'app'}": {
                        "__init__.py": "",
                        "main.py": "",
                        "api": {},
                        "models": {},
                        "services": {},
                        "utils": {},
                    }
                },
                "tests": {
                    "__init__.py": "",
                    "test_main.py": "",
                },
                "docs": {},
                "requirements.txt": "",
                "Dockerfile": "",
                "docker-compose.yml": "",
                "README.md": "",
            }
        elif template.runtime == "nodejs":
            return {
                "src": {
                    "index.ts": "",
                    "routes": {},
                    "controllers": {},
                    "models": {},
                    "services": {},
                    "utils": {},
                },
                "tests": {},
                "docs": {},
                "package.json": "",
                "tsconfig.json": "",
                "Dockerfile": "",
                "docker-compose.yml": "",
                "README.md": "",
            }
        elif template.runtime == "go":
            return {
                "cmd": {
                    "server": {"main.go": ""},
                },
                "internal": {
                    "handlers": {},
                    "models": {},
                    "services": {},
                    "repository": {},
                },
                "pkg": {},
                "tests": {},
                "go.mod": "",
                "Dockerfile": "",
                "docker-compose.yml": "",
                "README.md": "",
            }

        return {"src": {}, "tests": {}, "docs": {}}

    def generate_architecture_document(self, design: ArchitectureDesign) -> str:
        """
        生成架构设计文档 (Markdown)

        Args:
            design: 架构设计结果

        Returns:
            str: Markdown 格式的架构文档
        """
        doc = f"""# {design.project_name} - 架构设计文档

生成时间: {design.created_at.strftime("%Y-%m-%d %H:%M:%S")}

## 项目概述

{design.description}

## 技术栈

| 层级 | 技术 |
|------|------|
| 运行时 | {design.tech_stack.get('runtime', 'N/A')} |
| 前端 | {design.tech_stack.get('frontend') or 'N/A'} |
| 后端 | {design.tech_stack.get('backend') or 'N/A'} |
| 数据库 | {design.tech_stack.get('database') or 'N/A'} |

额外依赖: {', '.join(design.tech_stack.get('additional', [])) or '无'}

## 架构组件

"""
        for comp in design.components:
            doc += f"""### {comp.name}

- **类型**: {comp.type}
- **技术**: {comp.technology}
- **描述**: {comp.description}
- **连接**: {', '.join(comp.connections) or '无'}

"""

        if design.api_endpoints:
            doc += "## API 端点\n\n"
            for endpoint in design.api_endpoints:
                doc += f"- `{endpoint.get('method', 'GET')} {endpoint.get('path', '/')}` - {endpoint.get('description', '')}\n"
            doc += "\n"

        if design.data_models:
            doc += "## 数据模型\n\n"
            for model in design.data_models:
                doc += f"### {model.get('name', 'Unknown')}\n\n"
                for field in model.get("fields", []):
                    required = "必填" if field.get("required") else "可选"
                    doc += f"- `{field.get('name')}` ({field.get('type')}) - {required}\n"
                doc += "\n"

        doc += """## 目录结构

```
"""
        doc += self._format_directory_structure(design.directory_structure, "")
        doc += """```

## 部署配置

"""
        deploy = design.deployment
        doc += f"- Docker 支持: {'是' if deploy.get('docker') else '否'}\n"
        if deploy.get("ports"):
            doc += f"- 端口: {', '.join(map(str, deploy.get('ports')))}\n"
        if deploy.get("environment_vars"):
            doc += f"- 环境变量: {', '.join(deploy.get('environment_vars'))}\n"

        if design.recommendations:
            doc += "\n## 架构建议\n\n"
            for rec in design.recommendations:
                doc += f"- {rec}\n"

        return doc

    def _format_directory_structure(self, structure: dict, prefix: str) -> str:
        """格式化目录结构"""
        result = ""
        for name, content in structure.items():
            if isinstance(content, dict) and content:
                result += f"{prefix}{name}/\n"
                result += self._format_directory_structure(content, prefix + "  ")
            elif isinstance(content, dict):
                result += f"{prefix}{name}/\n"
            else:
                result += f"{prefix}{name}\n"
        return result

    def get_tech_recommendations(self, requirement: Requirement) -> dict:
        """
        获取技术栈推荐

        Args:
            requirement: 需求对象

        Returns:
            dict: 推荐结果
        """
        category = self._determine_category(requirement)
        scale = self._estimate_scale(requirement)
        templates = self.kb.recommend_for_project(category, scale)

        return {
            "category": category.value,
            "scale": scale.value,
            "templates": [
                {
                    "name": t.name,
                    "description": t.description,
                    "tech_stack": {
                        "runtime": t.runtime,
                        "frontend": t.frontend,
                        "backend": t.backend,
                        "database": t.database,
                    },
                    "use_cases": t.use_cases,
                }
                for t in templates
            ],
        }
