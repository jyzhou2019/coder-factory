"""
交付流水线 (F007)

构建完整的交付链：检查清单、文档生成、版本发布
"""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from datetime import datetime
from enum import Enum
import json
import re


class CheckStatus(Enum):
    """检查状态"""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CheckCategory(Enum):
    """检查类别"""
    CODE = "code"           # 代码质量
    TESTS = "tests"         # 测试覆盖
    DOCS = "docs"           # 文档完整性
    SECURITY = "security"   # 安全检查
    DEPLOY = "deploy"       # 部署就绪
    CONFIG = "config"       # 配置检查


@dataclass
class CheckItem:
    """检查项"""
    id: str
    name: str
    category: CheckCategory
    description: str
    status: CheckStatus = CheckStatus.PENDING
    message: str = ""
    required: bool = True
    auto_fix: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "status": self.status.value,
            "message": self.message,
            "required": self.required,
            "auto_fix": self.auto_fix,
        }


@dataclass
class DeliveryChecklist:
    """交付检查清单"""
    project_name: str
    version: str
    checks: list[CheckItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def passed_count(self) -> int:
        return len([c for c in self.checks if c.status == CheckStatus.PASSED])

    @property
    def failed_count(self) -> int:
        return len([c for c in self.checks if c.status == CheckStatus.FAILED])

    @property
    def is_ready(self) -> bool:
        """是否可以交付"""
        for check in self.checks:
            if check.required and check.status != CheckStatus.PASSED:
                return False
        return True

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "version": self.version,
            "checks": [c.to_dict() for c in self.checks],
            "summary": {
                "total": len(self.checks),
                "passed": self.passed_count,
                "failed": self.failed_count,
                "is_ready": self.is_ready,
            },
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ReleaseNote:
    """发布说明"""
    version: str
    date: datetime
    changes: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    fixes: list[str] = field(default_factory=list)
    breaking_changes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "date": self.date.isoformat(),
            "changes": self.changes,
            "features": self.features,
            "fixes": self.fixes,
            "breaking_changes": self.breaking_changes,
        }


# 默认检查项模板
DEFAULT_CHECKS: list[dict] = [
    # 代码质量
    {"id": "CODE-01", "name": "代码格式检查", "category": CheckCategory.CODE,
     "description": "代码格式符合规范", "required": True},
    {"id": "CODE-02", "name": "类型检查", "category": CheckCategory.CODE,
     "description": "类型注解完整且正确", "required": False},
    {"id": "CODE-03", "name": "Lint 检查", "category": CheckCategory.CODE,
     "description": "无 Lint 警告", "required": True},

    # 测试
    {"id": "TEST-01", "name": "单元测试", "category": CheckCategory.TESTS,
     "description": "单元测试通过", "required": True},
    {"id": "TEST-02", "name": "测试覆盖率", "category": CheckCategory.TESTS,
     "description": "测试覆盖率 >= 80%", "required": False},
    {"id": "TEST-03", "name": "集成测试", "category": CheckCategory.TESTS,
     "description": "集成测试通过", "required": False},

    # 文档
    {"id": "DOC-01", "name": "README 文档", "category": CheckCategory.DOCS,
     "description": "README.md 存在且完整", "required": True},
    {"id": "DOC-02", "name": "API 文档", "category": CheckCategory.DOCS,
     "description": "API 文档完整", "required": False},
    {"id": "DOC-03", "name": "CHANGELOG", "category": CheckCategory.DOCS,
     "description": "变更日志已更新", "required": True},

    # 安全
    {"id": "SEC-01", "name": "依赖安全检查", "category": CheckCategory.SECURITY,
     "description": "无已知安全漏洞", "required": True},
    {"id": "SEC-02", "name": "敏感信息检查", "category": CheckCategory.SECURITY,
     "description": "无敏感信息泄露", "required": True},

    # 部署
    {"id": "DEPLOY-01", "name": "Docker 构建", "category": CheckCategory.DEPLOY,
     "description": "Docker 镜像构建成功", "required": True},
    {"id": "DEPLOY-02", "name": "环境变量配置", "category": CheckCategory.DEPLOY,
     "description": "环境变量配置完整", "required": True},

    # 配置
    {"id": "CFG-01", "name": "版本号更新", "category": CheckCategory.CONFIG,
     "description": "版本号已更新", "required": True},
    {"id": "CFG-02", "name": "Git 状态干净", "category": CheckCategory.CONFIG,
     "description": "无未提交的更改", "required": True},
]


class ChecklistGenerator:
    """检查清单生成器"""

    def __init__(self):
        self.default_checks = DEFAULT_CHECKS

    def generate(self, project_name: str, version: str = "1.0.0") -> DeliveryChecklist:
        """生成交付检查清单"""
        checks = []
        for check_data in self.default_checks:
            check = CheckItem(
                id=check_data["id"],
                name=check_data["name"],
                category=check_data["category"],
                description=check_data["description"],
                required=check_data.get("required", True),
                auto_fix=check_data.get("auto_fix", False),
            )
            checks.append(check)

        return DeliveryChecklist(
            project_name=project_name,
            version=version,
            checks=checks,
        )

    def add_custom_check(
        self,
        checklist: DeliveryChecklist,
        name: str,
        category: CheckCategory,
        description: str,
        required: bool = True
    ) -> CheckItem:
        """添加自定义检查项"""
        check = CheckItem(
            id=f"CUSTOM-{len(checklist.checks) + 1:02d}",
            name=name,
            category=category,
            description=description,
            required=required,
        )
        checklist.checks.append(check)
        return check


class DocumentGenerator:
    """文档生成器"""

    def generate_readme(
        self,
        project_name: str,
        description: str,
        tech_stack: dict,
        features: list[str] | None = None,
        install_cmd: str | None = None,
        run_cmd: str | None = None
    ) -> str:
        """生成 README.md"""
        runtime = tech_stack.get("runtime", "python")
        backend = tech_stack.get("backend")
        database = tech_stack.get("database")

        # 确定安装命令
        if not install_cmd:
            if runtime == "python":
                install_cmd = "pip install -r requirements.txt"
            elif runtime == "nodejs":
                install_cmd = "npm install"
            elif runtime == "go":
                install_cmd = "go mod download"
            else:
                install_cmd = "请查看项目文档"

        # 确定运行命令
        if not run_cmd:
            if backend == "fastapi":
                run_cmd = "uvicorn main:app --reload"
            elif backend == "django":
                run_cmd = "python manage.py runserver"
            elif backend == "express":
                run_cmd = "npm start"
            elif runtime == "go":
                run_cmd = "go run ./cmd/server"
            else:
                run_cmd = "请查看项目文档"

        # 技术栈表格
        tech_table = f"| 运行时 | {runtime} |\n"
        if backend:
            tech_table += f"| 后端框架 | {backend} |\n"
        if tech_stack.get("frontend"):
            tech_table += f"| 前端框架 | {tech_stack['frontend']} |\n"
        if database:
            tech_table += f"| 数据库 | {database} |\n"

        # 功能列表
        features_md = ""
        if features:
            features_md = "\n## 功能特性\n\n" + "\n".join(f"- {f}" for f in features)

        return f"""# {project_name}

{description}

## 技术栈

| 组件 | 技术 |
|------|------|
{tech_table}
{features_md}

## 快速开始

### 环境要求

- {runtime.capitalize()} >= {"3.11" if runtime == "python" else "20" if runtime == "nodejs" else "1.21"}
{"- PostgreSQL >= 14" if database == "postgresql" else "- MongoDB >= 6.0" if database == "mongodb" else ""}

### 安装

```bash
{install_cmd}
```

### 运行

```bash
{run_cmd}
```

### Docker 部署

```bash
# 构建镜像
docker build -t {project_name}:latest .

# 使用 docker-compose 启动
docker-compose up -d
```

## 项目结构

```
{project_name}/
├── src/                # 源代码
├── tests/              # 测试文件
├── docs/               # 文档
├── Dockerfile          # Docker 配置
├── docker-compose.yml  # Docker Compose 配置
└── README.md           # 项目说明
```

## 开发指南

### 运行测试

```bash
{"pytest" if runtime == "python" else "npm test" if runtime == "nodejs" else "go test ./..."}
```

### 代码规范

{"请使用 black 和 isort 格式化代码" if runtime == "python" else "请使用 ESLint 和 Prettier" if runtime == "nodejs" else "请使用 gofmt 格式化代码"}

## 许可证

MIT License
"""

    def generate_changelog(
        self,
        project_name: str,
        releases: list[ReleaseNote] | None = None
    ) -> str:
        """生成 CHANGELOG.md"""
        lines = [
            f"# Changelog",
            "",
            f"All notable changes to {project_name} will be documented in this file.",
            "",
            "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),",
            "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
            "",
        ]

        if releases:
            for release in releases:
                lines.append(f"## [{release.version}] - {release.date.strftime('%Y-%m-%d')}")
                lines.append("")

                if release.features:
                    lines.append("### Added")
                    for feature in release.features:
                        lines.append(f"- {feature}")
                    lines.append("")

                if release.changes:
                    lines.append("### Changed")
                    for change in release.changes:
                        lines.append(f"- {change}")
                    lines.append("")

                if release.fixes:
                    lines.append("### Fixed")
                    for fix in release.fixes:
                        lines.append(f"- {fix}")
                    lines.append("")

                if release.breaking_changes:
                    lines.append("### Breaking Changes")
                    for bc in release.breaking_changes:
                        lines.append(f"- {bc}")
                    lines.append("")
        else:
            lines.extend([
                "## [Unreleased]",
                "",
                "### Added",
                "- 初始版本",
                "",
            ])

        return "\n".join(lines)

    def generate_api_docs(
        self,
        endpoints: list[dict],
        base_url: str = "http://localhost:8000"
    ) -> str:
        """生成 API 文档"""
        lines = [
            "# API Documentation",
            "",
            f"Base URL: `{base_url}`",
            "",
        ]

        # 按路径分组
        for endpoint in endpoints:
            method = endpoint.get("method", "GET")
            path = endpoint.get("path", "/")
            description = endpoint.get("description", "")
            params = endpoint.get("params", [])
            response = endpoint.get("response", {})

            lines.append(f"## `{method} {path}`")
            lines.append("")
            lines.append(f"**描述**: {description}")
            lines.append("")

            if params:
                lines.append("**参数**:")
                lines.append("")
                lines.append("| 参数名 | 类型 | 必需 | 描述 |")
                lines.append("|--------|------|------|------|")
                for param in params:
                    lines.append(f"| {param.get('name')} | {param.get('type')} | {'是' if param.get('required') else '否'} | {param.get('description', '')} |")
                lines.append("")

            if response:
                lines.append("**响应**:")
                lines.append("")
                lines.append("```json")
                lines.append(json.dumps(response, indent=2, ensure_ascii=False))
                lines.append("```")
                lines.append("")

        return "\n".join(lines)

    def generate_contributing(self, project_name: str, runtime: str = "python") -> str:
        """生成 CONTRIBUTING.md"""
        test_cmd = "pytest" if runtime == "python" else "npm test" if runtime == "nodejs" else "go test ./..."
        format_cmd = "black ." if runtime == "python" else "npm run format" if runtime == "nodejs" else "gofmt -w ."

        return f"""# Contributing to {project_name}

感谢你考虑为 {project_name} 做出贡献！

## 开发流程

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 代码规范

- 遵循项目现有的代码风格
- 添加必要的注释和文档
- 保持代码简洁清晰

## 测试

运行测试：
```bash
{test_cmd}
```

## 代码格式化

```bash
{format_cmd}
```

## 提交信息规范

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式（不影响代码运行的变动）
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

## 许可证

通过贡献代码，你同意你的贡献将按照 MIT 许可证授权。
"""


class ReleaseManager:
    """版本发布管理器"""

    def __init__(self, project_path: Path | str = "."):
        self.project_path = Path(project_path)

    def get_current_version(self) -> str:
        """获取当前版本"""
        # 尝试从 package.json 读取
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                return data.get("version", "0.1.0")
            except:
                pass

        # 尝试从 pyproject.toml 读取
        pyproject = self.project_path / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8")
                match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
            except:
                pass

        return "0.1.0"

    def bump_version(self, current: str, bump_type: str = "patch") -> str:
        """
        版本号递增

        Args:
            current: 当前版本
            bump_type: major/minor/patch

        Returns:
            str: 新版本号
        """
        # 解析版本号
        match = re.match(r"(\d+)\.(\d+)\.(\d+)", current)
        if not match:
            return "0.1.0"

        major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        return f"{major}.{minor}.{patch}"

    def create_release_note(
        self,
        version: str,
        features: list[str] | None = None,
        fixes: list[str] | None = None,
        changes: list[str] | None = None,
        breaking: list[str] | None = None
    ) -> ReleaseNote:
        """创建发布说明"""
        return ReleaseNote(
            version=version,
            date=datetime.now(),
            features=features or [],
            fixes=fixes or [],
            changes=changes or [],
            breaking_changes=breaking or [],
        )

    def generate_release_notes_md(self, release: ReleaseNote) -> str:
        """生成发布说明 Markdown"""
        lines = [
            f"# Release {release.version}",
            "",
            f"**发布日期**: {release.date.strftime('%Y-%m-%d')}",
            "",
        ]

        if release.features:
            lines.append("## ✨ 新功能")
            lines.append("")
            for feature in release.features:
                lines.append(f"- {feature}")
            lines.append("")

        if release.changes:
            lines.append("## 🔧 变更")
            lines.append("")
            for change in release.changes:
                lines.append(f"- {change}")
            lines.append("")

        if release.fixes:
            lines.append("## 🐛 修复")
            lines.append("")
            for fix in release.fixes:
                lines.append(f"- {fix}")
            lines.append("")

        if release.breaking_changes:
            lines.append("## ⚠️ 破坏性变更")
            lines.append("")
            for bc in release.breaking_changes:
                lines.append(f"- {bc}")
            lines.append("")

        return "\n".join(lines)


class DeliveryPipeline:
    """
    交付流水线

    整合检查清单、文档生成和版本发布
    """

    def __init__(self, project_path: Path | str = "."):
        self.project_path = Path(project_path)
        self.checklist_gen = ChecklistGenerator()
        self.doc_gen = DocumentGenerator()
        self.release_mgr = ReleaseManager(project_path)

    def create_checklist(self, project_name: str, version: str | None = None) -> DeliveryChecklist:
        """创建交付检查清单"""
        if not version:
            version = self.release_mgr.get_current_version()
        return self.checklist_gen.generate(project_name, version)

    def generate_all_docs(
        self,
        project_name: str,
        description: str,
        tech_stack: dict,
        features: list[str] | None = None,
        api_endpoints: list[dict] | None = None
    ) -> dict[str, str]:
        """
        生成所有文档

        Returns:
            dict[str, str]: 文件名 -> 内容
        """
        docs = {}

        # README
        docs["README.md"] = self.doc_gen.generate_readme(
            project_name=project_name,
            description=description,
            tech_stack=tech_stack,
            features=features,
        )

        # CHANGELOG
        docs["CHANGELOG.md"] = self.doc_gen.generate_changelog(project_name)

        # CONTRIBUTING
        runtime = tech_stack.get("runtime", "python")
        docs["CONTRIBUTING.md"] = self.doc_gen.generate_contributing(project_name, runtime)

        # API 文档
        if api_endpoints:
            docs["docs/API.md"] = self.doc_gen.generate_api_docs(api_endpoints)

        return docs

    def prepare_release(
        self,
        bump_type: str = "patch",
        features: list[str] | None = None,
        fixes: list[str] | None = None
    ) -> dict:
        """
        准备发布

        Args:
            bump_type: 版本递增类型
            features: 新功能列表
            fixes: 修复列表

        Returns:
            dict: 发布信息
        """
        current_version = self.release_mgr.get_current_version()
        new_version = self.release_mgr.bump_version(current_version, bump_type)
        release_note = self.release_mgr.create_release_note(
            version=new_version,
            features=features,
            fixes=fixes,
        )

        return {
            "current_version": current_version,
            "new_version": new_version,
            "release_note": release_note.to_dict(),
            "release_notes_md": self.release_mgr.generate_release_notes_md(release_note),
        }

    def get_delivery_summary(self, project_name: str) -> dict:
        """获取交付摘要"""
        checklist = self.create_checklist(project_name)
        version = self.release_mgr.get_current_version()

        return {
            "project_name": project_name,
            "current_version": version,
            "checklist_summary": {
                "total": len(checklist.checks),
                "passed": checklist.passed_count,
                "failed": checklist.failed_count,
                "is_ready": checklist.is_ready,
            },
            "generated_docs": ["README.md", "CHANGELOG.md", "CONTRIBUTING.md"],
            "next_steps": [
                "运行测试确保通过",
                "更新 CHANGELOG.md",
                "创建 Git 标签",
                "构建 Docker 镜像",
                "推送到 GitHub",
            ],
        }

    def write_docs(
        self,
        docs: dict[str, str],
        output_dir: Path | str | None = None
    ) -> list[Path]:
        """
        写入文档到文件

        Args:
            docs: 文档内容字典
            output_dir: 输出目录

        Returns:
            list[Path]: 写入的文件路径列表
        """
        output = Path(output_dir) if output_dir else self.project_path
        output.mkdir(parents=True, exist_ok=True)

        written_files = []
        for filename, content in docs.items():
            file_path = output / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            written_files.append(file_path)

        return written_files
