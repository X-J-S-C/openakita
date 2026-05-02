import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    print("=" * 60)
    print("🚀 OpenAkita: Akita-Evo 一键装机工具 (智能寻路版)")
    print("正在为你配置 AI 助手的运行环境...")
    print("=" * 60)

def find_project_root():
    """智能寻找项目根目录 (寻找 pyproject.toml)"""
    # 路径 A: 当前运行目录
    current_cwd = Path.cwd()
    if (current_cwd / "pyproject.toml").exists():
        return current_cwd

    # 路径 B: 脚本所在位置的父目录 (通常 scripts/ 在根目录下)
    script_dir = Path(__file__).resolve().parent.parent
    if (script_dir / "pyproject.toml").exists():
        print(f"💡 发现你在错误的文件夹运行。已自动为你定位到根目录: {script_dir}")
        return script_dir

    # 路径 C: 深度搜索 (防止解压后套娃: OpenAkita/OpenAkita/...)
    for p in current_cwd.rglob("pyproject.toml"):
        found_root = p.parent
        print(f"💡 发现项目图纸在深层目录。已自动定位: {found_root}")
        return found_root

    return None

def print_diagnostic_map():
    print("\n[🆘 诊断信息] 机器人找不到它的‘图纸’(pyproject.toml)了！")
    print("请检查你的文件夹是否长这样：")
    print("📂 Your-Folder/")
    print("├── 📄 pyproject.toml  <-- 关键文件！")
    print("├── 📂 src/")
    print("└── 📂 scripts/")
    print("\n[常见原因]：")
    print("1. 你可能只复制了 scripts 文件夹，没拿 pyproject.toml。")
    print("2. 你可能还没解压压缩包，直接在压缩软件里打开了。")
    print("3. 文件夹层级太深，请把解压后的内容移动到 D:\\OpenAkita 这种简单的路径下。")

def run_command(command, description, cwd=None):
    print(f"\n[正在执行] {description}...")
    try:
        # 使用当前 Python 解释器对应的 pip
        if "pip install" in command:
            cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
        else:
            cmd = command

        subprocess.check_call(cmd, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 执行失败: {description}")
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
        return

    # 2. 定位根目录
    root_dir = find_project_root()
    if not root_dir:
        print_diagnostic_map()
        return

    # 3. 确保安装命令在正确的根目录下执行
    os.chdir(root_dir)
    print(f"📍 当前工作目录: {os.getcwd()}")

    # 4. 安装依赖
    if not run_command("pip install -e .", "安装机器人组件与依赖库", cwd=root_dir):
        print("\n💡 提示：如果看到权限错误，请尝试用‘管理员身份’运行终端。")
        return

    print("\n✅ 环境安装完成！")
    time.sleep(1)

    # 5. 跳转到钥匙配置
    setup_script = root_dir / "scripts" / "setup_key.py"
    if setup_script.exists():
        print("\n[下一步] 正在为你开启“钥匙配置”程序...")
        time.sleep(1)
        subprocess.call([sys.executable, str(setup_script)])
    else:
        print("\n❌ 找不到 scripts/setup_key.py 文件，请检查是否完整解压。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[已取消] 安装被手动中断。")
