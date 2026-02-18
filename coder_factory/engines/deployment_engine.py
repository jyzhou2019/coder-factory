"""
容器化部署引擎 (F006)

自动生成 Dockerfile、docker-compose.yml 和部署脚本
"""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from datetime import datetime


@dataclass
class DockerConfig:
    """Docker 配置"""
    base_image: str
    workdir: str = "/app"
    expose_ports: list[int] = field(default_factory=list)
    environment_vars: dict[str, str] = field(default_factory=dict)
    volumes: list[str] = field(default_factory=list)
    commands: dict[str, str] = field(default_factory=dict)  # install, build, run, test
    health_check: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "base_image": self.base_image,
            "workdir": self.workdir,
            "expose_ports": self.expose_ports,
            "environment_vars": self.environment_vars,
            "volumes": self.volumes,
            "commands": self.commands,
            "health_check": self.health_check,
        }


@dataclass
class ComposeService:
    """Docker Compose 服务"""
    name: str
    build_context: str = "."
    dockerfile: str = "Dockerfile"
    ports: list[str] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)
    volumes: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    command: Optional[str] = None
    restart: str = "unless-stopped"

    def to_dict(self) -> dict:
        result = {
            "build": {
                "context": self.build_context,
                "dockerfile": self.dockerfile,
            },
            "restart": self.restart,
        }
        if self.ports:
            result["ports"] = self.ports
        if self.environment:
            result["environment"] = self.environment
        if self.volumes:
            result["volumes"] = self.volumes
        if self.depends_on:
            result["depends_on"] = self.depends_on
        if self.command:
            result["command"] = self.command
        return result


# 预定义的 Docker 配置模板
DOCKER_TEMPLATES: dict[str, DockerConfig] = {
    # Python 配置
    "python-fastapi": DockerConfig(
        base_image="python:3.11-slim",
        workdir="/app",
        expose_ports=[8000],
        commands={
            "install": "pip install --no-cache-dir -r requirements.txt",
            "run": "uvicorn main:app --host 0.0.0.0 --port 8000",
            "test": "pytest",
        },
        health_check="curl -f http://localhost:8000/health || exit 1",
    ),
    "python-django": DockerConfig(
        base_image="python:3.11-slim",
        workdir="/app",
        expose_ports=[8000],
        commands={
            "install": "pip install --no-cache-dir -r requirements.txt",
            "migrate": "python manage.py migrate",
            "run": "python manage.py runserver 0.0.0.0:8000",
            "test": "python manage.py test",
        },
    ),
    "python-cli": DockerConfig(
        base_image="python:3.11-slim",
        workdir="/app",
        commands={
            "install": "pip install --no-cache-dir -r requirements.txt",
            "run": "python main.py",
        },
    ),

    # Node.js 配置
    "nodejs-express": DockerConfig(
        base_image="node:20-alpine",
        workdir="/app",
        expose_ports=[3000],
        commands={
            "install": "npm ci",
            "build": "npm run build",
            "run": "npm start",
            "test": "npm test",
        },
        health_check="curl -f http://localhost:3000/health || exit 1",
    ),
    "nodejs-nestjs": DockerConfig(
        base_image="node:20-alpine",
        workdir="/app",
        expose_ports=[3000],
        commands={
            "install": "npm ci",
            "build": "npm run build",
            "run": "node dist/main",
            "test": "npm test",
        },
    ),
    "nodejs-react": DockerConfig(
        base_image="node:20-alpine",
        workdir="/app",
        expose_ports=[3000],
        commands={
            "install": "npm ci",
            "build": "npm run build",
            "run": "npm start",
        },
    ),

    # Go 配置
    "go-gin": DockerConfig(
        base_image="golang:1.21-alpine",
        workdir="/app",
        expose_ports=[8080],
        commands={
            "install": "go mod download",
            "build": "go build -o main ./cmd/server",
            "run": "./main",
            "test": "go test ./...",
        },
    ),
    "go-cli": DockerConfig(
        base_image="golang:1.21-alpine",
        workdir="/app",
        commands={
            "install": "go mod download",
            "build": "go build -o app ./cmd/app",
            "run": "./app",
        },
    ),

    # Rust 配置
    "rust-actix": DockerConfig(
        base_image="rust:1.74",
        workdir="/app",
        expose_ports=[8080],
        commands={
            "build": "cargo build --release",
            "run": "./target/release/app",
            "test": "cargo test",
        },
    ),
}


class DockerfileGenerator:
    """Dockerfile 生成器"""

    def __init__(self):
        self.templates = DOCKER_TEMPLATES

    def generate(
        self,
        tech_stack: dict,
        project_name: str = "app",
        include_dev: bool = True
    ) -> str:
        """
        生成 Dockerfile

        Args:
            tech_stack: 技术栈配置
            project_name: 项目名称
            include_dev: 是否包含开发环境

        Returns:
            str: Dockerfile 内容
        """
        runtime = tech_stack.get("runtime", "python")
        backend = tech_stack.get("backend")
        frontend = tech_stack.get("frontend")

        # 确定模板
        template_key = self._get_template_key(runtime, backend, frontend)
        config = self.templates.get(template_key, self._get_default_config(runtime))

        # 生成 Dockerfile
        lines = [
            f"# Dockerfile for {project_name}",
            f"# Generated by Coder-Factory at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # 多阶段构建 (生产优化)
        if include_dev:
            lines.extend(self._generate_dev_stage(config, project_name))
        else:
            lines.extend(self._generate_prod_stage(config, project_name))

        return "\n".join(lines)

    def _get_template_key(self, runtime: str, backend: str | None, frontend: str | None) -> str:
        """获取模板键"""
        if frontend:
            return f"{runtime}-{frontend}"
        if backend:
            return f"{runtime}-{backend}"
        return f"{runtime}-cli"

    def _get_default_config(self, runtime: str) -> DockerConfig:
        """获取默认配置"""
        if runtime == "nodejs":
            return DOCKER_TEMPLATES["nodejs-express"]
        elif runtime == "go":
            return DOCKER_TEMPLATES["go-gin"]
        elif runtime == "rust":
            return DOCKER_TEMPLATES["rust-actix"]
        return DOCKER_TEMPLATES["python-fastapi"]

    def _generate_dev_stage(self, config: DockerConfig, project_name: str) -> list[str]:
        """生成开发环境 Dockerfile"""
        lines = [
            f"FROM {config.base_image} AS base",
            "",
            f"WORKDIR {config.workdir}",
            "",
        ]

        # 安装系统依赖
        if "python" in config.base_image:
            lines.extend([
                "# Install system dependencies",
                "RUN apt-get update && apt-get install -y --no-install-recommends \\",
                "    curl \\",
                "    && rm -rf /var/lib/apt/lists/*",
                "",
            ])
        elif "node" in config.base_image:
            lines.extend([
                "# Install system dependencies",
                "RUN apk add --no-cache curl",
                "",
            ])

        # 复制依赖文件
        if "python" in config.base_image:
            lines.extend([
                "# Copy dependency files",
                "COPY requirements.txt .",
                "",
            ])
        elif "node" in config.base_image:
            lines.extend([
                "# Copy dependency files",
                "COPY package*.json ./",
                "",
            ])
        elif "go" in config.base_image:
            lines.extend([
                "# Copy dependency files",
                "COPY go.mod go.sum ./",
                "",
            ])

        # 安装依赖
        if config.commands.get("install"):
            lines.extend([
                "# Install dependencies",
                f"RUN {config.commands['install']}",
                "",
            ])

        # 复制源代码
        lines.extend([
            "# Copy source code",
            "COPY . .",
            "",
        ])

        # 构建命令
        if config.commands.get("build"):
            lines.extend([
                "# Build application",
                f"RUN {config.commands['build']}",
                "",
            ])

        # 暴露端口
        if config.expose_ports:
            ports = " ".join(str(p) for p in config.expose_ports)
            lines.extend([
                f"# Expose ports",
                f"EXPOSE {ports}",
                "",
            ])

        # 健康检查
        if config.health_check:
            lines.extend([
                "# Health check",
                f"HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\",
                f"    CMD {config.health_check}",
                "",
            ])

        # 默认命令
        if config.commands.get("run"):
            run_cmd = config.commands["run"]
            lines.extend([
                "# Default command",
                f'CMD ["sh", "-c", "{run_cmd}"]',
            ])

        return lines

    def _generate_prod_stage(self, config: DockerConfig, project_name: str) -> list[str]:
        """生成生产环境 Dockerfile (多阶段构建)"""
        lines = [
            "# Stage 1: Build",
            f"FROM {config.base_image} AS builder",
            "",
            f"WORKDIR {config.workdir}",
            "",
        ]

        # 构建阶段
        if "python" in config.base_image:
            lines.extend([
                "COPY requirements.txt .",
                f"RUN {config.commands.get('install', 'pip install -r requirements.txt')}",
                "COPY . .",
            ])
        elif "node" in config.base_image:
            lines.extend([
                "COPY package*.json ./",
                f"RUN {config.commands.get('install', 'npm ci')}",
                "COPY . .",
                f"RUN {config.commands.get('build', 'npm run build')}",
            ])
        elif "go" in config.base_image:
            lines.extend([
                "COPY go.mod go.sum ./",
                f"RUN {config.commands.get('install', 'go mod download')}",
                "COPY . .",
                f"RUN {config.commands.get('build', 'go build -o main ./...')}",
            ])

        # 运行阶段
        lines.extend([
            "",
            "# Stage 2: Runtime",
        ])

        if "python" in config.base_image:
            lines.append("FROM python:3.11-slim AS runtime")
        elif "node" in config.base_image:
            lines.append("FROM node:20-alpine AS runtime")
        elif "go" in config.base_image:
            lines.append("FROM alpine:3.18 AS runtime")
        else:
            lines.append(f"FROM {config.base_image} AS runtime")

        lines.extend([
            "",
            f"WORKDIR {config.workdir}",
            "",
        ])

        # 复制构建产物
        if "python" in config.base_image:
            lines.extend([
                "COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages",
                "COPY --from=builder /app .",
            ])
        elif "node" in config.base_image:
            lines.extend([
                "COPY --from=builder /app/node_modules ./node_modules",
                "COPY --from=builder /app/dist ./dist",
                "COPY --from=builder /app/package*.json ./",
            ])
        elif "go" in config.base_image:
            lines.extend([
                "RUN apk add --no-cache ca-certificates",
                "COPY --from=builder /app/main .",
            ])

        # 端口和命令
        if config.expose_ports:
            lines.extend(["", f"EXPOSE {' '.join(str(p) for p in config.expose_ports)}"])

        if config.commands.get("run"):
            lines.extend(["", f'CMD ["sh", "-c", "{config.commands["run"]}"]'])

        return lines


class DockerComposeGenerator:
    """Docker Compose 生成器"""

    def generate(
        self,
        project_name: str,
        tech_stack: dict,
        include_database: bool = True,
        include_redis: bool = False,
        dev_mode: bool = True
    ) -> str:
        """
        生成 docker-compose.yml

        Args:
            project_name: 项目名称
            tech_stack: 技术栈配置
            include_database: 是否包含数据库
            include_redis: 是否包含 Redis
            dev_mode: 是否为开发模式

        Returns:
            str: docker-compose.yml 内容
        """
        services = []
        backend_name = project_name.replace("-", "_").lower()

        # 主服务
        main_service = ComposeService(
            name=backend_name,
            build_context=".",
            ports=self._get_main_ports(tech_stack),
            environment=self._get_main_env(tech_stack, dev_mode),
            volumes=[".:/app"] if dev_mode else [],
        )

        if dev_mode:
            main_service.command = self._get_dev_command(tech_stack)

        services.append(main_service)

        # 数据库服务
        if include_database:
            db_service = self._get_database_service(tech_stack, backend_name)
            if db_service:
                services.append(db_service)
                main_service.depends_on.append(db_service.name)
                main_service.environment.update(self._get_db_env(tech_stack))

        # Redis 服务
        if include_redis:
            redis_service = ComposeService(
                name="redis",
                build_context="",  # 使用镜像
                ports=["6379:6379"],
            )
            # 修改为使用镜像
            services.append(redis_service)

        # 生成 YAML
        return self._generate_yaml(project_name, services, dev_mode)

    def _get_main_ports(self, tech_stack: dict) -> list[str]:
        """获取主服务端口映射"""
        runtime = tech_stack.get("runtime", "python")
        backend = tech_stack.get("backend")

        if backend == "fastapi" or backend == "django":
            return ["8000:8000"]
        elif backend == "express" or backend == "nestjs":
            return ["3000:3000"]
        elif runtime == "go":
            return ["8080:8080"]
        elif tech_stack.get("frontend"):
            return ["3000:3000"]
        return []

    def _get_main_env(self, tech_stack: dict, dev_mode: bool) -> dict[str, str]:
        """获取主服务环境变量"""
        env = {
            "NODE_ENV": "development" if dev_mode else "production",
            "PYTHONUNBUFFERED": "1",
        }
        return env

    def _get_dev_command(self, tech_stack: dict) -> str:
        """获取开发模式命令"""
        runtime = tech_stack.get("runtime", "python")
        backend = tech_stack.get("backend")

        if backend == "fastapi":
            return "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
        elif backend == "django":
            return "python manage.py runserver 0.0.0.0:8000"
        elif backend == "express":
            return "npm run dev"
        elif backend == "nestjs":
            return "npm run start:dev"
        elif runtime == "go":
            return "go run ./cmd/server"
        return ""

    def _get_database_service(self, tech_stack: dict, backend_name: str) -> Optional[ComposeService]:
        """获取数据库服务"""
        database = tech_stack.get("database")

        if database == "postgresql":
            return ComposeService(
                name="db",
                build_context="",  # 使用镜像
                ports=["5432:5432"],
                environment={
                    "POSTGRES_USER": backend_name,
                    "POSTGRES_PASSWORD": "password",
                    "POSTGRES_DB": backend_name,
                },
                volumes=[f"postgres_data:/var/lib/postgresql/data"],
            )
        elif database == "mongodb":
            return ComposeService(
                name="mongodb",
                build_context="",
                ports=["27017:27017"],
                environment={
                    "MONGO_INITDB_ROOT_USERNAME": "admin",
                    "MONGO_INITDB_ROOT_PASSWORD": "password",
                },
                volumes=["mongo_data:/data/db"],
            )
        elif database == "mysql":
            return ComposeService(
                name="mysql",
                build_context="",
                ports=["3306:3306"],
                environment={
                    "MYSQL_ROOT_PASSWORD": "password",
                    "MYSQL_DATABASE": backend_name,
                },
                volumes=["mysql_data:/var/lib/mysql"],
            )

        return None

    def _get_db_env(self, tech_stack: dict) -> dict[str, str]:
        """获取数据库连接环境变量"""
        database = tech_stack.get("database")
        env = {}

        if database == "postgresql":
            env.update({
                "DATABASE_URL": "postgresql://app:password@db:5432/app",
            })
        elif database == "mongodb":
            env.update({
                "MONGODB_URI": "mongodb://admin:password@mongodb:27017",
            })
        elif database == "mysql":
            env.update({
                "DATABASE_URL": "mysql://root:password@mysql:3306/app",
            })

        return env

    def _generate_yaml(self, project_name: str, services: list[ComposeService], dev_mode: bool) -> str:
        """生成 YAML 内容"""
        lines = [
            f"# Docker Compose for {project_name}",
            f"# Generated by Coder-Factory",
            "",
            "services:",
        ]

        for service in services:
            lines.extend(self._generate_service_yaml(service))

        # Volumes
        volumes = []
        for service in services:
            for vol in service.volumes:
                if ":" in vol and not vol.startswith("."):
                    vol_name = vol.split(":")[0]
                    if vol_name not in volumes:
                        volumes.append(vol_name)

        if volumes:
            lines.extend(["", "volumes:"])
            for vol in volumes:
                lines.append(f"  {vol}:")

        return "\n".join(lines)

    def _generate_service_yaml(self, service: ComposeService) -> list[str]:
        """生成服务 YAML"""
        lines = [
            f"  {service.name}:",
        ]

        data = service.to_dict()

        # Build
        if "build" in data:
            lines.append(f"    build:")
            lines.append(f"      context: {data['build']['context']}")
            lines.append(f"      dockerfile: {data['build']['dockerfile']}")

        # Ports
        if "ports" in data:
            lines.append("    ports:")
            for port in data["ports"]:
                lines.append(f'      - "{port}"')

        # Environment
        if "environment" in data:
            lines.append("    environment:")
            for key, value in data["environment"].items():
                lines.append(f'      - {key}={value}')

        # Volumes
        if "volumes" in data:
            lines.append("    volumes:")
            for vol in data["volumes"]:
                lines.append(f'      - {vol}')

        # Depends on
        if "depends_on" in data:
            lines.append("    depends_on:")
            for dep in data["depends_on"]:
                lines.append(f"      - {dep}")

        # Command
        if "command" in data:
            lines.append(f'    command: {data["command"]}')

        # Restart
        lines.append(f"    restart: {service.restart}")

        lines.append("")
        return lines


class DeploymentEngine:
    """
    部署引擎

    核心功能：
    1. 生成 Dockerfile
    2. 生成 docker-compose.yml
    3. 生成部署脚本
    4. 执行部署命令
    """

    def __init__(self, workspace: Path | str = "./workspace"):
        self.workspace = Path(workspace)
        self.dockerfile_gen = DockerfileGenerator()
        self.compose_gen = DockerComposeGenerator()

    def generate_dockerfile(
        self,
        tech_stack: dict,
        project_name: str = "app",
        prod: bool = False
    ) -> str:
        """生成 Dockerfile"""
        return self.dockerfile_gen.generate(tech_stack, project_name, include_dev=not prod)

    def generate_compose(
        self,
        project_name: str,
        tech_stack: dict,
        include_database: bool = True,
        dev_mode: bool = True
    ) -> str:
        """生成 docker-compose.yml"""
        return self.compose_gen.generate(
            project_name,
            tech_stack,
            include_database=include_database,
            dev_mode=dev_mode
        )

    def generate_deploy_script(self, project_name: str) -> str:
        """生成部署脚本"""
        return f'''#!/bin/bash
# Deploy script for {project_name}
# Generated by Coder-Factory

set -e

echo "Building {project_name}..."

# Build Docker image
docker build -t {project_name}:latest .

# Stop existing containers
docker-compose down 2>/dev/null || true

# Start services
docker-compose up -d

echo "Deployment complete!"
echo "Check status: docker-compose ps"
echo "View logs: docker-compose logs -f"
'''

    def generate_env_example(self, tech_stack: dict) -> str:
        """生成 .env.example 文件"""
        lines = [
            "# Environment Variables",
            "# Copy this file to .env and fill in the values",
            "",
            "# Application",
            "NODE_ENV=development",
            "DEBUG=true",
            "",
        ]

        database = tech_stack.get("database")
        if database == "postgresql":
            lines.extend([
                "# PostgreSQL",
                "DATABASE_URL=postgresql://user:password@localhost:5432/dbname",
                "POSTGRES_USER=user",
                "POSTGRES_PASSWORD=password",
                "POSTGRES_DB=dbname",
                "",
            ])
        elif database == "mongodb":
            lines.extend([
                "# MongoDB",
                "MONGODB_URI=mongodb://localhost:27017/dbname",
                "",
            ])
        elif database == "mysql":
            lines.extend([
                "# MySQL",
                "DATABASE_URL=mysql://user:password@localhost:3306/dbname",
                "",
            ])

        lines.extend([
            "# Security",
            "SECRET_KEY=your-secret-key-here",
            "",
            "# External Services (optional)",
            "# REDIS_URL=redis://localhost:6379",
        ])

        return "\n".join(lines)

    def generate_dockerignore(self, tech_stack: dict) -> str:
        """生成 .dockerignore 文件"""
        runtime = tech_stack.get("runtime", "python")

        common = [
            "# Git",
            ".git",
            ".gitignore",
            "",
            "# Documentation",
            "*.md",
            "docs/",
            "",
            "# IDE",
            ".vscode",
            ".idea",
            "*.swp",
            "",
            "# OS",
            ".DS_Store",
            "Thumbs.db",
            "",
            "# Docker",
            "docker-compose*.yml",
            ".dockerignore",
            "",
        ]

        if runtime == "python":
            return "\n".join(common + [
                "# Python",
                "__pycache__",
                "*.py[cod]",
                "*$py.class",
                ".Python",
                "venv/",
                ".venv/",
                "env/",
                "*.egg-info/",
                ".pytest_cache/",
                ".coverage",
                "htmlcov/",
            ])
        elif runtime == "nodejs":
            return "\n".join(common + [
                "# Node.js",
                "node_modules",
                "npm-debug.log*",
                "yarn-debug.log*",
                "yarn-error.log*",
                ".npm",
                ".yarn-integrity",
                "dist/",
                "build/",
                ".next/",
            ])
        elif runtime == "go":
            return "\n".join(common + [
                "# Go",
                "*.exe",
                "*.exe~",
                "*.dll",
                "*.so",
                "*.dylib",
                "*.test",
                "*.out",
                "vendor/",
            ])

        return "\n".join(common)

    def write_deployment_files(
        self,
        project_name: str,
        tech_stack: dict,
        output_dir: Path | str | None = None
    ) -> dict[str, Path]:
        """
        写入所有部署文件

        Args:
            project_name: 项目名称
            tech_stack: 技术栈配置
            output_dir: 输出目录

        Returns:
            dict[str, Path]: 生成的文件路径
        """
        output = Path(output_dir) if output_dir else self.workspace
        output.mkdir(parents=True, exist_ok=True)

        files = {}

        # Dockerfile
        dockerfile_path = output / "Dockerfile"
        dockerfile_path.write_text(self.generate_dockerfile(tech_stack, project_name))
        files["dockerfile"] = dockerfile_path

        # docker-compose.yml
        compose_path = output / "docker-compose.yml"
        compose_path.write_text(self.generate_compose(project_name, tech_stack))
        files["docker_compose"] = compose_path

        # .dockerignore
        dockerignore_path = output / ".dockerignore"
        dockerignore_path.write_text(self.generate_dockerignore(tech_stack))
        files["dockerignore"] = dockerignore_path

        # .env.example
        env_path = output / ".env.example"
        env_path.write_text(self.generate_env_example(tech_stack))
        files["env_example"] = env_path

        # deploy.sh
        deploy_path = output / "deploy.sh"
        deploy_path.write_text(self.generate_deploy_script(project_name))
        files["deploy_script"] = deploy_path

        return files

    def get_deployment_summary(self, project_name: str, tech_stack: dict) -> dict:
        """获取部署摘要"""
        return {
            "project_name": project_name,
            "tech_stack": tech_stack,
            "files": [
                "Dockerfile",
                "docker-compose.yml",
                ".dockerignore",
                ".env.example",
                "deploy.sh",
            ],
            "commands": {
                "build": f"docker build -t {project_name}:latest .",
                "run": "docker-compose up -d",
                "stop": "docker-compose down",
                "logs": "docker-compose logs -f",
                "ps": "docker-compose ps",
            },
        }
