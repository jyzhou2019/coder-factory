"""
Coder-Factory CLI 入口

底层使用 Claude Code 完成实际工作
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.prompt import Confirm

from . import __version__
from .core.factory import CoderFactory, ProcessResult


console = Console()


@click.group(invoke_without_command=True)
@click.option('--version', '-v', is_flag=True, help='显示版本信息')
@click.option('--interactive', '-i', is_flag=True, help='启动交互模式')
@click.pass_context
def cli(ctx, version, interactive):
    """Coder-Factory: AI自主代码工厂 (底层使用 Claude Code)"""
    if version:
        console.print(f"[bold green]Coder-Factory[/] v{__version__}")
        return

    if interactive or ctx.invoked_subcommand is None:
        ctx.invoke(run_interactive)


@cli.command()
def run_interactive():
    """启动交互式会话"""
    console.print(Panel.fit(
        "[bold cyan]Coder-Factory[/] - AI自主代码工厂\n"
        f"版本: {__version__}\n"
        "[dim]底层使用 Claude Code 完成需求解析和代码生成[/]",
        title="欢迎",
        border_style="cyan"
    ))

    factory = CoderFactory()

    while True:
        try:
            console.print("\n[bold yellow]请描述您的需求[/] (输入 'exit' 退出):")
            user_input = console.input("[green]>>> [/]")

            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("[dim]再见！[/]")
                break

            if user_input.strip():
                result = factory.process_requirement(user_input)
                _display_parse_result(result, factory)

                if result.success:
                    if Confirm.ask("\n是否生成代码?"):
                        gen_result = factory.generate_code(confirm=False)
                        if gen_result.success:
                            console.print(f"[green]✓ 代码生成完成![/]")
                            if Confirm.ask("是否运行测试?"):
                                test_result = factory.run_tests()
                                console.print(f"{'[green]✓[/]' if test_result.success else '[red]✗[/]'} 测试{'通过' if test_result.success else '失败'}")
                        else:
                            console.print(f"[red]✗ 代码生成失败:[/] {gen_result.error}")

        except KeyboardInterrupt:
            console.print("\n[dim]已取消[/]")
            break
        except Exception as e:
            console.print(f"[red]错误: {e}[/]")


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

    # 显示待确认问题
    questions = summary.get('clarification_questions', [])
    if questions:
        console.print("\n[yellow]待确认问题:[/]")
        for i, q in enumerate(questions, 1):
            console.print(f"  {i}. {q.get('question', q)}")


@cli.command()
@click.argument('requirement')
@click.option('--output', '-o', default='./workspace', help='输出目录')
@click.option('--generate', '-g', is_flag=True, help='解析后直接生成代码')
def parse(requirement, output, generate):
    """解析需求并显示任务分解"""
    console.print(f"[cyan]正在解析需求...[/]")

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
def generate(requirement, output):
    """根据需求生成代码 (解析 -> 生成 -> 测试)"""
    console.print(f"[cyan]正在处理需求:[/] {requirement[:50]}...")

    factory = CoderFactory(output_dir=output)

    # Step 1: 解析
    with console.status("[bold green]解析需求..."):
        result = factory.process_requirement(requirement)

    if not result.success:
        console.print(f"[red]✗ 需求解析失败:[/] {result.error}")
        return

    console.print(f"[green]✓ 需求已解析[/]")

    # Step 2: 生成
    with console.status("[bold green]生成代码..."):
        gen_result = factory.generate_code(confirm=False)

    if not gen_result.success:
        console.print(f"[red]✗ 代码生成失败:[/] {gen_result.error}")
        return

    console.print(f"[green]✓ 代码生成完成[/]")

    # Step 3: 测试
    with console.status("[bold green]运行测试..."):
        test_result = factory.run_tests()

    if test_result.success:
        console.print(f"[green]✓ 测试通过[/]")
    else:
        console.print(f"[yellow]⚠ 测试失败:[/] {test_result.error}")

    console.print(f"\n[bold green]✓ 完成![/] 输出目录: {output}")


@cli.command()
def status():
    """显示当前状态"""
    table = Table(title="Coder-Factory 模块状态")
    table.add_column("模块", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("说明", style="dim")

    modules = [
        ("F001 需求解析引擎", "✓ 已实现", "使用 Claude Code 解析"),
        ("F002 交互确认系统", "待开发", "多轮对话确认"),
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


if __name__ == '__main__':
    cli()
