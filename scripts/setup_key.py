import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

def setup_key():
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]🔑 OpenAkita 机器人“开启钥匙”配置工具[/bold cyan]\n"
        "[dim]帮助机器人连通大脑（大模型）[/dim]",
        border_style="cyan"
    ))

    console.print("\n[yellow]💡 什么是“开启钥匙” (API Key)？[/yellow]")
    console.print("这就像是给机器人充值的“话费卡”或“身份证”。有了它，机器人才能调用像 Claude 或 DeepSeek 这样强大的大脑来为你工作。")

    env_path = Path(".env")
    existing_content = ""
    if env_path.exists():
        existing_content = env_path.read_text(encoding="utf-8")

    # 引导用户选择提供商
    console.print("\n[bold]1. 你打算使用哪家的大脑？[/bold]")
    provider = Prompt.ask(
        "请选择 (输入数字)",
        choices=["Anthropic (Claude)", "DeepSeek (国产性价比之王)", "OpenAI (GPT)"],
        default="DeepSeek (国产性价比之王)"
    )

    key_name = ""
    if "Anthropic" in provider:
        key_name = "ANTHROPIC_API_KEY"
        link = "https://console.anthropic.com/"
    elif "DeepSeek" in provider:
        key_name = "DEEPSEEK_API_KEY"
        link = "https://platform.deepseek.com/"
    else:
        key_name = "OPENAI_API_KEY"
        link = "https://platform.openai.com/"

    console.print(f"\n[bold]2. 请去这里获取你的钥匙：[/bold] [underline blue]{link}[/underline blue]")
    api_key = Prompt.ask(f"请粘贴你获取到的 [bold green]{key_name}[/bold green] (输入后看不见是正常的，直接回车即可)", password=True)

    if not api_key:
        console.print("[red]❌ 钥匙不能为空，配置失败。[/red]")
        return

    # 生成或更新 .env 文件
    new_line = f"{key_name}={api_key}\n"

    # 简单的逻辑：如果 key 已存在则替换，否则追加
    lines = []
    found = False
    if existing_content:
        for line in existing_content.splitlines():
            if line.startswith(f"{key_name}="):
                lines.append(new_line.strip())
                found = True
            else:
                lines.append(line)

    if not found:
        lines.append(new_line.strip())

    # 默认设置一些对新手友好的配置
    if "DEEPSEEK" in key_name and "OPENAKITA_DEFAULT_MODEL" not in existing_content:
        lines.append("OPENAKITA_DEFAULT_MODEL=deepseek-chat")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    console.print(f"\n[bold green]🎉 恭喜！钥匙已存入“秘密纸条”(.env 文件)！[/bold green]")
    console.print("现在机器人已经可以听懂你的指令了。")

    if Confirm.ask("\n是否立刻开启功能导览，看看机器人的超能力？"):
        console.print("\n[bold yellow]正在启动导览脚本...[/bold yellow]")
        os.system(f"{sys.executable} scripts/evo_tour.py")

if __name__ == "__main__":
    import sys
    try:
        setup_key()
    except KeyboardInterrupt:
        console.print("\n[red]已退出配置。[/red]")
