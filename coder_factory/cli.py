"""
Coder-Factory CLI 入口

底层使用 Claude Code 完成实际工作
"""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.prompt import Confirm, Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .core.factory import CoderFactory, ProcessResult
from .engines.confirmation_flow import ConfirmationFlow
from .engines.interaction_manager import QuestionType
from .engines.architecture_designer import ArchitectureDesigner
from .engines.tech_stack_kb import TechStackKnowledgeBase, ProjectCategory
from .engines.deployment_engine import DeploymentEngine
from .engines.delivery_pipeline import DeliveryPipeline, CheckStatus


console = Console()


@click.group(invoke_without_command=True)
@click.option('--version', '-v', is_flag=True, help='显示版本信息')
@click.option('--interactive', '-i', is_flag=True, help='启动交互模式')
@click.option('--skip-confirm', '-y', is_flag=True, help='跳过确认直接生成')
@click.pass_context
def cli(ctx, version, interactive, skip_confirm):
    """Coder-Factory: AI自主代码工厂 (底层使用 Claude Code)"""
    if version:
        console.print(f"[bold green]Coder-Factory[/] v{__version__}")
        return

    if interactive or ctx.invoked_subcommand is None:
        ctx.invoke(run_interactive, skip_confirm=skip_confirm)


@cli.command()
@click.option('--skip-confirm', '-y', is_flag=True, help='跳过确认直接生成')
def run_interactive(skip_confirm):
    """启动交互式会话"""
    console.print(Panel.fit(
        "[bold cyan]Coder-Factory[/] - AI自主代码工厂\n"
        f"版本: {__version__}\n"
        "[dim]底层使用 Claude Code 完成需求解析和代码生成[/]\n"
        "[dim]输入 'exit' 退出, 'help' 查看帮助[/]",
        title="欢迎",
        border_style="cyan"
    ))

    while True:
        try:
            console.print("\n[bold yellow]请描述您的需求[/]:")
            user_input = console.input("[green]>>> [/]")

            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("[dim]再见！[/]")
                break

            if user_input.lower() == 'help':
                _show_help()
                continue

            if user_input.lower() == 'status':
                _show_status()
                continue

            if user_input.strip():
                _run_workflow(user_input, skip_confirm)

        except KeyboardInterrupt:
            console.print("\n[dim]已取消[/]")
            break
        except Exception as e:
            console.print(f"[red]错误: {e}[/]")


def _run_workflow(requirement: str, skip_confirm: bool = False):
    """运行完整工作流"""
    flow = ConfirmationFlow()

    # Step 1: 解析需求
    with console.status("[bold green]解析需求..."):
        result = flow.start(requirement)

    if not result.get("success"):
        console.print(f"[red]✗ 需求解析失败:[/] {result.get('error')}")
        return

    console.print(f"[green]✓ 需求已解析:[/] {result.get('summary')}")

    # 显示需求摘要
    _display_requirement_summary(result)

    # Step 2: 交互确认
    if not skip_confirm:
        confirm_result = _run_confirmation(flow)
        if not confirm_result:
            return
    else:
        # 跳过确认，直接批准
        flow.approve()

    # Step 3: 生成代码
    console.print("\n[cyan]准备生成代码...[/]")
    if Confirm.ask("是否开始生成代码?"):
        factory = CoderFactory()
        with console.status("[bold green]生成代码..."):
            gen_result = factory.generate_code(confirm=False)

        if gen_result.success:
            console.print(f"[green]✓ 代码生成完成![/]")

            if Confirm.ask("是否运行测试?"):
                with console.status("[bold green]运行测试..."):
                    test_result = factory.run_tests()
                if test_result.success:
                    console.print(f"[green]✓ 测试通过[/]")
                else:
                    console.print(f"[yellow]⚠ 测试失败:[/] {test_result.error}")
        else:
            console.print(f"[red]✗ 代码生成失败:[/] {gen_result.error}")


def _display_requirement_summary(result: dict):
    """显示需求摘要"""
    console.print(Panel(
        f"[bold]项目类型:[/] {result.get('project_type', 'unknown')}\n"
        f"[bold]核心功能:[/]\n" + "\n".join(f"  • {f}" for f in result.get('features', [])),
        title="需求摘要",
        border_style="blue"
    ))


def _run_confirmation(flow: ConfirmationFlow) -> bool:
    """运行交互确认流程"""
    console.print("\n[cyan]━━━ 需求确认阶段 ━━━[/]")

    while True:
        question = flow.get_current_question()

        if question is None:
            # 所有问题已回答
            break

        # 显示问题
        answer = _ask_question(question)

        if answer is None:
            # 用户取消
            if Confirm.ask("确定要取消吗?"):
                flow.cancel("用户取消")
                console.print("[yellow]已取消[/]")
                return False
            continue

        # 记录答案
        result = flow.answer(answer)

        if result.get("state") == "refining":
            # 进入优化阶段
            break

    # 显示最终需求并请求批准
    console.print("\n[cyan]━━━ 最终确认 ━━━[/]")
    final_req = flow.get_status().get("requirement", {})

    table = Table(title="最终需求")
    table.add_column("字段", style="cyan")
    table.add_column("值", style="green")

    for key, value in final_req.items():
        if isinstance(value, (list, dict)):
            value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
        table.add_row(key, str(value))

    console.print(table)

    # 变更历史
    changes = flow.manager.get_change_history()
    if changes:
        console.print(f"\n[dim]变更记录: {len(changes)} 条[/]")

    if Confirm.ask("\n[bold green]批准此需求并开始生成代码?[/]"):
        result = flow.approve()
        if result.get("success"):
            console.print("[green]✓ 需求已批准[/]")
            return True
        else:
            console.print(f"[red]✗ 批准失败:[/] {result.get('error')}")
            return False
    else:
        # 提供修改选项
        if Confirm.ask("是否需要修改需求?"):
            field = Prompt.ask("请输入要修改的字段名")
            new_value = Prompt.ask("请输入新值")
            flow.modify(field, new_value, "用户修改")
            return _run_confirmation(flow)  # 重新确认
        else:
            flow.cancel("用户拒绝")
            console.print("[yellow]已取消[/]")
            return False


def _ask_question(question: dict) -> any:
    """询问用户问题"""
    q_type = question.get("type", "confirm")
    q_text = question.get("question", "")
    options = question.get("options", [])
    default = question.get("default")

    console.print(f"\n[yellow]?[/] {q_text}")

    try:
        if q_type == "confirm":
            return Confirm.ask("", default=default if default is not None else True)

        elif q_type == "choice":
            for i, opt in enumerate(options, 1):
                console.print(f"  [dim]{i}[/] {opt}")

            choice = Prompt.ask(
                "请选择",
                choices=[str(i) for i in range(1, len(options) + 1)],
                default="1"
            )
            return options[int(choice) - 1]

        elif q_type == "multi_select":
            for i, opt in enumerate(options, 1):
                console.print(f"  [dim]{i}[/] {opt}")

            choices_str = Prompt.ask(
                "请选择 (多个用逗号分隔)",
                default="1"
            )
            indices = [int(x.strip()) for x in choices_str.split(",")]
            return [options[i - 1] for i in indices if 0 < i <= len(options)]

        elif q_type == "text":
            return Prompt.ask("请输入", default=default or "")

        elif q_type == "number":
            while True:
                try:
                    return int(Prompt.ask("请输入数字", default=str(default or 0)))
                except ValueError:
                    console.print("[red]请输入有效的数字[/]")

    except KeyboardInterrupt:
        return None


@cli.command()
@click.argument('requirement')
@click.option('--output', '-o', default='./workspace', help='输出目录')
@click.option('--generate', '-g', is_flag=True, help='解析后直接生成代码')
@click.option('--confirm/--no-confirm', default=True, help='是否进行交互确认')
def parse(requirement, output, generate, confirm):
    """解析需求并显示任务分解"""
    console.print(f"[cyan]正在解析需求...[/]")

    if confirm:
        flow = ConfirmationFlow(output)
        result = flow.start(requirement)

        if not result.get("success"):
            console.print(f"[red]✗ 需求解析失败:[/] {result.get('error')}")
            return

        _display_requirement_summary(result)

        if _run_confirmation(flow):
            console.print(f"[green]✓ 需求已确认[/]")

            if generate:
                factory = CoderFactory(output_dir=output)
                gen_result = factory.generate_code(confirm=False)
                if gen_result.success:
                    console.print(f"[green]✓ 代码生成完成![/] 输出目录: {output}")
                else:
                    console.print(f"[red]✗ 代码生成失败:[/] {gen_result.error}")
    else:
        factory = CoderFactory(output_dir=output)
        result = factory.process_requirement(requirement)
        _display_parse_result(result, factory)

        if generate and result.success:
            console.print("\n[cyan]正在生成代码...[/]")
            gen_result = factory.generate_code(confirm=False)
            if gen_result.success:
                console.print(f"[green]✓ 代码生成完成![/] 输出目录: {output}")
            else:
                console.print(f"[red]✗ 代码生成失败:[/] {gen_result.error}")


@cli.command()
@click.argument('requirement')
@click.option('--output', '-o', default='./workspace', help='输出目录')
@click.option('--skip-confirm', '-y', is_flag=True, help='跳过确认直接生成')
def generate(requirement, output, skip_confirm):
    """根据需求生成代码 (解析 -> 确认 -> 生成 -> 测试)"""
    _run_workflow(requirement, skip_confirm)


@cli.command()
def status():
    """显示当前状态"""
    _show_status()


@cli.command()
@click.argument('requirement')
@click.option('--output', '-o', default='./workspace', help='输出目录')
@click.option('--save-doc', '-s', is_flag=True, help='保存架构文档')
def design(requirement, output, save_doc):
    """设计系统架构 (技术栈推荐 + 架构设计)"""
    console.print(f"[cyan]正在设计架构...[/]")

    # 解析需求
    from .engines.requirement_parser import RequirementParser
    parser = RequirementParser(output)
    parse_result = parser.parse(requirement)

    if not parse_result.success:
        console.print(f"[red]✗ 需求解析失败:[/] {parse_result.error}")
        return

    req = parse_result.requirement
    console.print(f"[green]✓ 需求已解析:[/] {req.summary}")

    # 获取技术推荐
    designer = ArchitectureDesigner(output)
    recommendations = designer.get_tech_recommendations(req)

    # 显示推荐
    console.print(f"\n[bold]项目类型:[/] {recommendations['category']}")
    console.print(f"[bold]规模估算:[/] {recommendations['scale']}")

    if recommendations['templates']:
        console.print("\n[bold cyan]推荐技术栈:[/]")
        for i, template in enumerate(recommendations['templates'][:3], 1):
            console.print(Panel(
                f"[bold]{template['name']}[/]\n"
                f"{template['description']}\n\n"
                f"[dim]运行时:[/] {template['tech_stack'].get('runtime', 'N/A')}\n"
                f"[dim]前端:[/] {template['tech_stack'].get('frontend') or 'N/A'}\n"
                f"[dim]后端:[/] {template['tech_stack'].get('backend') or 'N/A'}\n"
                f"[dim]数据库:[/] {template['tech_stack'].get('database') or 'N/A'}\n"
                f"[dim]适用场景:[/] {', '.join(template['use_cases'])}",
                title=f"方案 {i}",
                border_style="blue"
            ))

    # 完整架构设计
    console.print("\n[cyan]正在生成详细架构...[/]")
    arch_design = designer.analyze_and_design(req)

    # 显示架构组件
    if arch_design.components:
        console.print("\n[bold cyan]架构组件:[/]")
        for comp in arch_design.components:
            console.print(f"  [green]•[/] [bold]{comp.name}[/] ({comp.type})")
            console.print(f"    [dim]技术:[/] {comp.technology}")
            if comp.connections:
                console.print(f"    [dim]连接:[/] {', '.join(comp.connections)}")

    # 显示 API 端点
    if arch_design.api_endpoints:
        console.print(f"\n[bold cyan]API 端点:[/] ({len(arch_design.api_endpoints)} 个)")
        for endpoint in arch_design.api_endpoints[:5]:
            console.print(f"  [yellow]{endpoint.get('method', 'GET')}[/] {endpoint.get('path', '/')}")

    # 显示建议
    if arch_design.recommendations:
        console.print("\n[bold cyan]架构建议:[/]")
        for rec in arch_design.recommendations:
            console.print(f"  [dim]•[/] {rec}")

    # 保存文档
    if save_doc:
        doc = designer.generate_architecture_document(arch_design)
        doc_path = Path(output) / "ARCHITECTURE.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(doc, encoding="utf-8")
        console.print(f"\n[green]✓ 架构文档已保存:[/] {doc_path}")


@cli.command()
@click.argument('tech_names', required=False)
def tech(tech_names):
    """查看技术栈信息

    示例:
      coder-factory tech              # 列出所有技术
      coder-factory tech python       # 查看 Python 信息
      coder-factory tech python,go    # 比较多个技术
    """
    kb = TechStackKnowledgeBase()

    if not tech_names:
        # 显示所有技术
        console.print("[bold cyan]可用运行时:[/]")
        for rt in kb.get_all_runtimes():
            opt = kb.get_option(rt)
            if opt:
                console.print(f"  [green]•[/] {opt.name} - 复杂度:{opt.complexity} 流行度:{opt.popularity}")

        console.print("\n[bold cyan]可用后端框架:[/]")
        for fw in kb.get_all_frameworks("backend"):
            opt = kb.get_option(fw)
            if opt:
                console.print(f"  [green]•[/] {opt.name} - {', '.join(opt.best_for[:2])}")

        console.print("\n[bold cyan]可用数据库:[/]")
        for db in kb.get_all_databases():
            opt = kb.get_option(db)
            if opt:
                console.print(f"  [green]•[/] {opt.name} - {', '.join(opt.best_for[:2])}")

        console.print("\n[dim]使用 'coder-factory tech <名称>' 查看详情[/]")
    else:
        names = [n.strip().lower() for n in tech_names.split(",")]
        if len(names) == 1:
            # 显示单个技术详情
            opt = kb.get_option(names[0])
            if opt:
                console.print(Panel(
                    f"[bold]优点:[/]\n" + "\n".join(f"  [green]+[/] {p}" for p in opt.pros) +
                    f"\n\n[bold]缺点:[/]\n" + "\n".join(f"  [red]-[/] {c}" for c in opt.cons) +
                    f"\n\n[bold]适用场景:[/]\n" + "\n".join(f"  • {u}" for u in opt.best_for) +
                    f"\n\n[bold]评分:[/] 复杂度 {opt.complexity}/5 | 流行度 {opt.popularity}/5 | 性能 {opt.performance}/5",
                    title=opt.name,
                    border_style="cyan"
                ))
            else:
                console.print(f"[red]未找到技术: {names[0]}[/]")
        else:
            # 比较多个技术
            comparison = kb.compare_techs(names)
            if comparison:
                table = Table(title="技术对比")
                table.add_column("指标", style="cyan")
                for name in comparison:
                    table.add_column(name, style="green")

                for metric in ["complexity", "popularity", "performance"]:
                    row = [metric]
                    for name in comparison:
                        row.append(str(comparison[name][metric]))
                    table.add_row(*row)

                console.print(table)
            else:
                console.print("[red]未找到任何匹配的技术[/]")


@cli.command()
@click.argument('project_path', default='.')
@click.option('--runtime', '-r', default='python', help='运行时 (python/nodejs/go)')
@click.option('--backend', '-b', default=None, help='后端框架')
@click.option('--frontend', '-f', default=None, help='前端框架')
@click.option('--database', '-d', default=None, help='数据库')
@click.option('--output', '-o', default=None, help='输出目录')
@click.option('--prod', is_flag=True, help='生成生产环境配置')
def deploy(project_path, runtime, backend, frontend, database, output, prod):
    """生成 Docker 部署配置

    示例:
      coder-factory deploy                              # 使用默认配置
      coder-factory deploy . -r python -b fastapi       # Python FastAPI
      coder-factory deploy . -r nodejs -b express       # Node.js Express
      coder-factory deploy . -r python -d postgresql    # 带数据库
      coder-factory deploy . --prod                     # 生产环境
    """
    console.print("[cyan]生成 Docker 部署配置...[/]")

    # 构建技术栈
    tech_stack = {
        "runtime": runtime,
        "backend": backend,
        "frontend": frontend,
        "database": database,
    }

    # 确定输出目录
    output_dir = Path(output) if output else Path(project_path)

    # 生成部署配置
    engine = DeploymentEngine(output_dir)
    project_name = output_dir.name or "app"

    # 生成文件
    files = engine.write_deployment_files(project_name, tech_stack, output_dir)

    # 显示结果
    console.print(f"\n[green]✓ 已生成以下文件:[/]")
    for name, path in files.items():
        console.print(f"  [dim]•[/] {path.name}")

    # 显示使用说明
    summary = engine.get_deployment_summary(project_name, tech_stack)
    console.print(f"\n[bold cyan]使用方法:[/]")
    for cmd_name, cmd in summary["commands"].items():
        console.print(f"  [dim]{cmd_name}:[/] {cmd}")

    if prod:
        console.print(f"\n[yellow]注意: 生产环境配置已启用，请确保:[/]")
        console.print("  • 修改 .env.example 为 .env 并填写真实值")
        console.print("  • 检查 Dockerfile 中的安全配置")
        console.print("  • 配置适当的健康检查")


@cli.command()
@click.argument('project_path', default='.')
@click.option('--build', is_flag=True, help='构建镜像')
@click.option('--up', is_flag=True, help='启动服务')
@click.option('--down', is_flag=True, help='停止服务')
@click.option('--logs', is_flag=True, help='查看日志')
def docker(project_path, build, up, down, logs):
    """Docker 操作命令

    示例:
      coder-factory docker --build    # 构建镜像
      coder-factory docker --up       # 启动服务
      coder-factory docker --down     # 停止服务
      coder-factory docker --logs     # 查看日志
    """
    import subprocess

    project_dir = Path(project_path)

    if build:
        console.print("[cyan]构建 Docker 镜像...[/]")
        result = subprocess.run(
            ["docker", "build", "-t", f"{project_dir.name}:latest", "."],
            cwd=project_dir,
        )
        if result.returncode == 0:
            console.print("[green]✓ 构建完成[/]")
        else:
            console.print("[red]✗ 构建失败[/]")

    elif up:
        console.print("[cyan]启动服务...[/]")
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=project_dir,
        )
        if result.returncode == 0:
            console.print("[green]✓ 服务已启动[/]")
            console.print("[dim]查看状态: docker-compose ps[/]")

    elif down:
        console.print("[cyan]停止服务...[/]")
        result = subprocess.run(
            ["docker-compose", "down"],
            cwd=project_dir,
        )
        console.print("[green]✓ 服务已停止[/]")

    elif logs:
        subprocess.run(
            ["docker-compose", "logs", "-f"],
            cwd=project_dir,
        )

    else:
        console.print("[yellow]请指定操作: --build, --up, --down, --logs[/]")


@cli.command()
@click.argument('project_path', default='.')
@click.option('--checklist', is_flag=True, help='生成交付检查清单')
@click.option('--docs', is_flag=True, help='生成项目文档')
@click.option('--release', is_flag=True, help='准备版本发布')
@click.option('--bump', type=click.Choice(['major', 'minor', 'patch']), default='patch', help='版本递增类型')
@click.option('--output', '-o', default=None, help='输出目录')
def deliver(project_path, checklist, docs, release, bump, output):
    """交付流水线操作

    示例:
      coder-factory deliver --checklist     # 生成检查清单
      coder-factory deliver --docs          # 生成文档
      coder-factory deliver --release       # 准备发布
      coder-factory deliver --release --bump minor  # 小版本发布
    """
    pipeline = DeliveryPipeline(project_path)
    project_name = Path(project_path).name or "project"
    output_dir = Path(output) if output else Path(project_path)

    if checklist:
        console.print("[cyan]生成交付检查清单...[/]")
        cl = pipeline.create_checklist(project_name)

        table = Table(title=f"交付检查清单 - {project_name} v{cl.version}")
        table.add_column("ID", style="dim")
        table.add_column("检查项", style="cyan")
        table.add_column("类别", style="yellow")
        table.add_column("状态", style="green")
        table.add_column("必需", style="dim")

        for check in cl.checks:
            status_style = {
                CheckStatus.PASSED: "[green]✓[/]",
                CheckStatus.FAILED: "[red]✗[/]",
                CheckStatus.SKIPPED: "[dim]-[/]",
                CheckStatus.PENDING: "[yellow]?[/]",
            }.get(check.status, "?")

            table.add_row(
                check.id,
                check.name,
                check.category.value,
                status_style,
                "是" if check.required else "否"
            )

        console.print(table)
        console.print(f"\n[bold]总计:[/] {len(cl.checks)} 项")
        console.print(f"[green]通过:[/] {cl.passed_count}  [red]失败:[/] {cl.failed_count}")
        console.print(f"[bold]交付就绪:[/] {'[green]是[/]' if cl.is_ready else '[red]否[/]'}")

    elif docs:
        console.print("[cyan]生成项目文档...[/]")

        # 获取技术栈信息
        tech_stack = {"runtime": "python"}  # 默认值
        description = f"{project_name} 项目"

        # 生成文档
        generated_docs = pipeline.generate_all_docs(
            project_name=project_name,
            description=description,
            tech_stack=tech_stack,
        )

        # 写入文件
        written = pipeline.write_docs(generated_docs, output_dir)

        console.print(f"[green]✓ 已生成 {len(written)} 个文档文件:[/]")
        for f in written:
            console.print(f"  [dim]•[/] {f.name}")

    elif release:
        console.print("[cyan]准备版本发布...[/]")

        release_info = pipeline.prepare_release(bump_type=bump)

        console.print(f"\n[bold]版本变更:[/]")
        console.print(f"  当前版本: [yellow]{release_info['current_version']}[/]")
        console.print(f"  新版本: [green]{release_info['new_version']}[/]")

        console.print(f"\n[bold]发布说明:[/]")
        console.print(Panel(release_info['release_notes_md'], border_style="green"))

        console.print(f"\n[bold]下一步:[/]")
        console.print("  1. 更新版本号到配置文件")
        console.print("  2. 更新 CHANGELOG.md")
        console.print(f"  3. git tag v{release_info['new_version']}")
        console.print("  4. git push --tags")

    else:
        # 显示交付摘要
        summary = pipeline.get_delivery_summary(project_name)
        console.print(Panel(
            f"[bold]项目:[/] {summary['project_name']}\n"
            f"[bold]版本:[/] {summary['current_version']}\n"
            f"[bold]检查项:[/] {summary['checklist_summary']['total']} 项\n"
            f"[bold]文档:[/] {', '.join(summary['generated_docs'])}\n",
            title="交付摘要",
            border_style="cyan"
        ))
        console.print("\n[bold]可用操作:[/]")
        console.print("  --checklist  生成交付检查清单")
        console.print("  --docs       生成项目文档")
        console.print("  --release    准备版本发布")


def _show_status():
    """显示模块状态"""
    table = Table(title="Coder-Factory 模块状态")
    table.add_column("模块", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("说明", style="dim")

    modules = [
        ("F001 需求解析引擎", "✓ 已实现", "使用 Claude Code 解析"),
        ("F002 交互确认系统", "✓ 已实现", "多轮对话确认"),
        ("F003 架构设计引擎", "✓ 已实现", "技术栈知识库 + 架构生成"),
        ("F004 代码生成核心", "✓ 已实现", "使用 Claude Code 生成"),
        ("F005 自动化测试系统", "✓ 已实现", "使用 Claude Code 测试"),
        ("F006 容器化部署引擎", "✓ 已实现", "Dockerfile + Compose 自动生成"),
        ("F007 交付流水线", "✓ 已实现", "检查清单 + 文档 + 发布"),
    ]

    for name, status, desc in modules:
        style = "green" if "✓" in status else "dim"
        table.add_row(name, f"[{style}]{status}[/]", desc)

    console.print(table)


def _show_help():
    """显示帮助信息"""
    console.print(Panel(
        "[bold]命令:[/]\n"
        "  [cyan]exit[/] - 退出程序\n"
        "  [cyan]help[/] - 显示帮助\n"
        "  [cyan]status[/] - 显示模块状态\n"
        "\n[bold]直接输入需求描述[/] 即可开始生成代码\n"
        "\n[bold]示例:[/]\n"
        "  [dim]创建一个用户管理系统，支持登录、注册和个人信息管理[/]",
        title="帮助",
        border_style="yellow"
    ))


def _display_parse_result(result: ProcessResult, factory: CoderFactory):
    """显示需求解析结果"""
    if not result.success:
        console.print(f"[red]✗ 需求解析失败:[/] {result.error}")
        return

    console.print(f"\n[green]✓ 需求已解析:[/] {result.message}")

    summary = factory.get_task_summary()

    # 显示需求摘要
    console.print(Panel(
        f"[bold]项目类型:[/] {summary.get('project_type', 'unknown')}\n"
        f"[bold]核心功能:[/]\n" + "\n".join(f"  • {f}" for f in summary.get('features', [])),
        title="需求摘要",
        border_style="blue"
    ))

    # 显示任务树
    if result.requirement and result.requirement.task_tree:
        tree = Tree("[bold]任务分解[/]")
        for task in result.requirement.task_tree.subtasks:
            task_node = tree.add(f"[cyan]{task.title}[/] [{task.priority.value}]")
            for subtask in task.subtasks:
                task_node.add(f"[dim]{subtask.title}[/]")
        console.print(tree)


if __name__ == '__main__':
    cli()
