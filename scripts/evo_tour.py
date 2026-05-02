import os
import sys
import time
import asyncio
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn

# 模拟环境设置
os.environ["EVOLUTION_DRY_RUN"] = "true"

console = Console()

async def run_tour():
    console.clear()
    console.print(Panel.fit("[bold magenta]🌟 Akita-Evo 沉浸式功能导览 🌟[/bold magenta]\n[dim]零基础新手体验脚本 v1.0[/dim]", border_style="magenta"))

    # 步骤 1: 演示影子实验室
    with console.status("[bold blue]🧪 演示：影子实验室 (Shadow Workspace)...[/bold blue]") as status:
        time.sleep(2)
        console.print("✅ [green]拦截成功！[/green] Agent 尝试修改 'README.md'，系统已自动重定向。")
        console.print("🔗 [blue]操作路径：[/blue] .openakita/shadow/tour_task/README.md")
        console.print("🌳 [dim]可视化操作树已生成：[/dim]")
        console.print("   └── [WRITE] README.md (已添加新手引导标志)")

    time.sleep(1.5)

    # 步骤 2: 演示自愈进化
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task1 = progress.add_task(description="🧬 正在模拟“代码缺陷”自愈循环...", total=100)
        time.sleep(2)
        progress.update(task1, advance=40, description="❌ [red]验证失败：[/red] 发现逻辑死循环")
        time.sleep(1.5)
        progress.update(task1, advance=30, description="🛠️ [yellow]正在自愈：[/yellow] DeepSeek 模型正在重写 SOP...")
        time.sleep(2)
        progress.update(task1, advance=30, description="✅ [green]修复成功！[/green] 新技能已结晶。")

    time.sleep(1.5)

    # 步骤 3: 展示可视化仪表盘
    console.print("\n[bold green]📊 演示：知识全景图 (Dashboard)[/bold green]")
    with console.status("[bold cyan]🎨 正在绘制高保真仪表盘...[/bold cyan]") as status:
        # 这里实际上会调用 generate_dashboard，演示脚本中模拟路径输出
        plot_path = Path("data/audit_plots/audit_dashboard.png")
        time.sleep(2)
        console.print(f"✅ [green]绘制完成！[/green] 仪表盘已保存至：[bold underline]{plot_path}[/bold underline]")

    console.print(Panel("\n[bold yellow]体验结束！[/bold yellow]\n\n现在你可以运行 [bold cyan]openakita chat[/bold cyan] 开始你的真实旅程了。\n\n[dim]想要了解更多？请阅读 GUIDE_FOR_BEGINNERS.md[/dim]", border_style="yellow"))

if __name__ == "__main__":
    try:
        asyncio.run(run_tour())
    except KeyboardInterrupt:
        console.print("\n[red]已手动退出导览。[/red]")
