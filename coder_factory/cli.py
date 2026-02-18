"""
Coder-Factory CLI 入口

底层使用 Claude Code 完成实际工作
"""

import click
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


def _show_status():
    """显示模块状态"""
    table = Table(title="Coder-Factory 模块状态")
    table.add_column("模块", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("说明", style="dim")

    modules = [
        ("F001 需求解析引擎", "✓ 已实现", "使用 Claude Code 解析"),
        ("F002 交互确认系统", "✓ 已实现", "多轮对话确认"),
        ("F003 架构设计引擎", "待开发", "技术栈匹配"),
        ("F004 代码生成核心", "✓ 已实现", "使用 Claude Code 生成"),
        ("F005 自动化测试系统", "✓ 已实现", "使用 Claude Code 测试"),
        ("F006 容器化部署引擎", "待开发", "Docker 部署"),
        ("F007 交付流水线", "待开发", "完整交付链"),
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
