"""
Claude Code 集成客户端

通过子进程调用 Claude Code CLI，实现需求解析和代码生成
"""

import subprocess
import json
import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class ClaudeCodeResult:
    """Claude Code 执行结果"""
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0


class ClaudeCodeClient:
    """
    Claude Code 客户端

    封装对 Claude Code CLI 的调用，提供：
    - 需求解析
    - 代码生成
    - 测试执行
    - 部署操作
    """

    def __init__(self, workspace: Path | str = "./workspace"):
        self.workspace = Path(workspace)
        self.claude_cmd = "claude"

    def _run_command(
        self,
        prompt: str,
        timeout: int = 300,
        extra_args: list[str] | None = None
    ) -> ClaudeCodeResult:
        """
        执行 Claude Code 命令

        Args:
            prompt: 提示词
            timeout: 超时时间(秒)
            extra_args: 额外参数

        Returns:
            ClaudeCodeResult: 执行结果
        """
        args = [self.claude_cmd, "--print", prompt]
        if extra_args:
            args.extend(extra_args)

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.workspace),
                env={**os.environ, "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", "")}
            )

            return ClaudeCodeResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.stderr else None,
                exit_code=result.returncode
            )

        except subprocess.TimeoutExpired:
            return ClaudeCodeResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds",
                exit_code=-1
            )
        except FileNotFoundError:
            return ClaudeCodeResult(
                success=False,
                output="",
                error="Claude Code CLI not found. Please install it first.",
                exit_code=-1
            )

    def parse_requirement(self, requirement: str) -> dict:
        """
        使用 Claude Code 解析用户需求

        Args:
            requirement: 用户需求描述

        Returns:
            dict: 解析后的结构化需求
        """
        parse_prompt = f"""请分析以下用户需求，并以 JSON 格式输出结构化结果。

用户需求：
{requirement}

请输出以下 JSON 结构（不要输出其他内容，只输出 JSON）：
{{
    "summary": "需求摘要（一句话）",
    "project_type": "项目类型（web/api/cli/mobile/library等）",
    "features": ["核心功能1", "核心功能2", ...],
    "constraints": ["约束条件1", "约束条件2", ...],
    "suggested_tech_stack": {{
        "runtime": "python/nodejs/go/rust",
        "frontend": "react/vue/svelte/none",
        "backend": "fastapi/django/express/gin/none",
        "database": "postgresql/mongodb/sqlite/none"
    }},
    "tasks": [
        {{
            "title": "任务标题",
            "type": "setup/frontend/backend/database/api/testing/deployment",
            "priority": "P0/P1/P2/P3",
            "description": "任务描述",
            "subtasks": ["子任务1", "子任务2"]
        }}
    ],
    "questions": [
        "需要向用户确认的问题1",
        "需要向用户确认的问题2"
    ]
}}"""

        result = self._run_command(parse_prompt, timeout=120)

        if result.success:
            try:
                # 尝试从输出中提取 JSON
                output = result.output.strip()
                # 处理可能的 markdown 代码块
                if "```json" in output:
                    output = output.split("```json")[1].split("```")[0]
                elif "```" in output:
                    output = output.split("```")[1].split("```")[0]

                return json.loads(output.strip())
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse JSON response",
                    "raw_output": result.output
                }
        else:
            return {
                "error": result.error,
                "success": False
            }

    def generate_code(self, spec: dict, output_dir: str | None = None) -> ClaudeCodeResult:
        """
        使用 Claude Code 生成代码

        Args:
            spec: 项目规格
            output_dir: 输出目录

        Returns:
            ClaudeCodeResult: 生成结果
        """
        target_dir = output_dir or str(self.workspace)

        generate_prompt = f"""请根据以下项目规格生成完整的代码实现。

项目规格：
{json.dumps(spec, ensure_ascii=False, indent=2)}

要求：
1. 在 {target_dir} 目录下创建项目结构
2. 生成所有必要的源代码文件
3. 创建 Dockerfile 和 docker-compose.yml
4. 添加 README.md 说明文档
5. 确保代码可以直接运行

请开始生成代码。"""

        return self._run_command(generate_prompt, timeout=600)

    def run_tests(self, project_dir: str) -> ClaudeCodeResult:
        """
        使用 Claude Code 运行测试

        Args:
            project_dir: 项目目录

        Returns:
            ClaudeCodeResult: 测试结果
        """
        test_prompt = f"""请在 {project_dir} 目录中：
1. 检查是否有测试文件
2. 运行所有测试
3. 报告测试结果

如果测试失败，请分析原因并尝试修复。"""

        return self._run_command(test_prompt, timeout=300)

    def deploy(self, project_dir: str, method: str = "docker") -> ClaudeCodeResult:
        """
        使用 Claude Code 执行部署

        Args:
            project_dir: 项目目录
            method: 部署方式 (docker/local)

        Returns:
            ClaudeCodeResult: 部署结果
        """
        deploy_prompt = f"""请在 {project_dir} 目录中执行部署：
1. 构建项目
2. 使用 {method} 方式部署
3. 验证部署是否成功
4. 报告部署状态和访问方式"""

        return self._run_command(deploy_prompt, timeout=300)
