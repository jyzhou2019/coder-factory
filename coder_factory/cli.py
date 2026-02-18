"""
Coder-Factory CLI 入口
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .core.factory import CoderFactory


console = Console()


@click.group(invoke_without_command=True)
@click.option('--version', '-v', is_flag=True, help='显示版本信息')
@click.option('--interactive', '-i', is_flag=True, help='启动交互模式')
@click.pass_context
def cli(ctx, version, interactive):
    """Coder-Factory: AI自主代码工厂"""
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
        "从需求到交付的全自动化生产线",
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
                factory.process_requirement(user_input)

        except KeyboardInterrupt:
            console.print("\n[dim]已取消[/]")
            break
        except Exception as e:
            console.print(f"[red]错误: {e}[/]")


@cli.command()
@click.argument('requirement')
@click.option('--output', '-o', default='./workspace', help='输出目录')
def generate(requirement, output):
    """根据需求生成代码"""
    console.print(f"[cyan]正在处理需求:[/] {requirement}")

    factory = CoderFactory(output_dir=output)
    result = factory.process_requirement(requirement)

    if result.success:
        console.print(f"[green]✓ 生成完成![/] 输出目录: {output}")
    else:
        console.print(f"[red]✗ 生成失败:[/] {result.error}")


@cli.command()
def status():
    """显示当前状态"""
    table = Table(title="Coder-Factory 状态")
    table.add_column("模块", style="cyan")
    table.add_column("状态", style="green")

    modules = [
        ("需求解析引擎", "待开发"),
        ("交互确认系统", "待开发"),
        ("架构设计引擎", "待开发"),
        ("代码生成核心", "待开发"),
        ("自动化测试系统", "待开发"),
        ("容器化部署引擎", "待开发"),
        ("交付流水线", "待开发"),
    ]

    for name, status in modules:
        table.add_row(name, f"[dim]{status}[/]")

    console.print(table)


if __name__ == '__main__':
    cli()
