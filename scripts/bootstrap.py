import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    print("=" * 60)
    print("🚀 OpenAkita: Akita-Evo 一键装机工具")
    print("正在为你配置 AI 助手的运行环境...")
    print("=" * 60)

def run_command(command, description):
    print(f"\n[正在执行] {description}...")
    try:
        # 使用当前 Python 解释器对应的 pip
        cmd = [sys.executable, "-m", "pip", "install", "-e", "."] if "pip install" in command else command
        subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 执行失败: {description}")
        print(f"错误码: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ 发生意外错误: {e}")
        return False

def main():
    print_banner()

    # 1. 检查 Python 版本
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("\n❌ 你的 Python 版本太低了！")
        print(f"当前版本: {version.major}.{version.minor}")
        print("Akita-Evo 需要 Python 3.11 或更高版本。")
        print("请去 https://www.python.org/ 下载最新版。")
        return

    # 2. 安装依赖
    if not run_command("pip install -e .", "安装机器人组件与依赖库"):
        print("\n💡 提示：如果安装失败，请尝试在终端运行: pip install -e . --user")
        return

    print("\n✅ 环境安装完成！")
    time.sleep(1)

    # 3. 跳转到钥匙配置
    setup_script = Path("scripts/setup_key.py")
    if setup_script.exists():
        print("\n[下一步] 正在为你开启“钥匙配置”程序...")
        time.sleep(1)
        # 运行配置脚本
        subprocess.call([sys.executable, str(setup_script)])
    else:
        print("\n❌ 找不到 scripts/setup_key.py 文件，请检查是否完整解压。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[已取消] 安装被手动中断。")
