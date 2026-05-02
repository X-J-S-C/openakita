"""
TDD 开发工作流脚本

提供 TDD 周期的辅助命令。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_command(cmd: list[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """运行命令"""
    return subprocess.run(cmd, cwd=cwd or Path.cwd())


def run_tests(pattern: str = "test_*.py", verbose: bool = True) -> int:
    """运行测试"""
    cmd = ["python", "-m", "pytest"]
    if verbose:
        cmd.append("-v")
    cmd.extend(["-k", pattern])
    result = run_command(cmd)
    return result.returncode


def run_tests_with_coverage(module: str = "architecture") -> int:
    """运行测试并生成覆盖率报告"""
    cmd = [
        "python", "-m", "pytest",
        "-v",
        "--cov=src/openakita/" + module,
        "--cov-report=term-missing",
        "--cov-report=html",
    ]
    result = run_command(cmd)
    if result.returncode == 0:
        print("\n覆盖率报告已生成: coverage_html/index.html")
    return result.returncode


def run_contract_tests() -> int:
    """运行契约测试"""
    cmd = [
        "python", "-m", "pytest",
        "-v",
        "-m", "contract",
    ]
    return run_command(cmd).returncode


def run_unit_tests() -> int:
    """运行单元测试"""
    cmd = [
        "python", "-m", "pytest",
        "-v",
        "-m", "unit",
    ]
    return run_command(cmd).returncode


def create_test_file(module_name: str, class_name: str) -> Path:
    """创建新的测试文件"""
    test_dir = Path("tests") / "architecture"
    test_file = test_dir / f"test_{module_name}.py"

    if test_file.exists():
        print(f"测试文件已存在: {test_file}")
        return test_file

    content = f'''"""
{module_name} TDD 测试

遵循 TDD 流程：Red-Green-Refactor
测试 {class_name} 的核心功能。
"""

from __future__ import annotations

import pytest


class Test{class_name}:
    """Test {class_name}"""

    def test_placeholder(self):
        """占位测试"""
        assert True
'''
    test_file.write_text(content)
    print(f"创建测试文件: {test_file}")
    return test_file


def create_unit_test(module_path: str, function_name: str) -> None:
    """创建单元测试"""
    print(f"创建单元测试: {module_path}.{function_name}")


def tdd_cycle(module: str, test_name: str) -> None:
    """
    执行一个 TDD 周期

    1. 写一个失败的测试 (RED)
    2. 实现代码使其通过 (GREEN)
    3. 重构代码 (REFACTOR)
    """
    print(f"\n{'='*60}")
    print(f"TDD 周期: {module}.{test_name}")
    print(f"{'='*60}\n")

    print("1. RED - 写失败的测试")
    print("-" * 40)
    run_tests(pattern=test_name)

    print("\n2. GREEN - 实现代码")
    print("-" * 40)
    print("> 在对应的模块中实现代码...")

    print("\n3. GREEN - 再次运行测试")
    print("-" * 40)
    result = run_tests(pattern=test_name)

    if result == 0:
        print("\n✅ 测试通过!")
        print("\n4. REFACTOR - 重构（如需要）")
        print("-" * 40)
        print("> 检查代码质量，优化实现...")
    else:
        print("\n❌ 测试失败!")
        sys.exit(1)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="TDD 开发工作流")
    parser.add_argument("command", choices=[
        "test", "test-verbose", "coverage", "contract", "unit", "create-test", "tdd"
    ])
    parser.add_argument("--module", default="architecture")
    parser.add_argument("--test", default="")
    parser.add_argument("--class-name", default="")

    args = parser.parse_args()

    if args.command == "test":
        sys.exit(run_tests())
    elif args.command == "test-verbose":
        sys.exit(run_tests(verbose=True))
    elif args.command == "coverage":
        sys.exit(run_tests_with_coverage(args.module))
    elif args.command == "contract":
        sys.exit(run_contract_tests())
    elif args.command == "unit":
        sys.exit(run_unit_tests())
    elif args.command == "create-test":
        if not args.class_name:
            print("错误: 需要 --class-name 参数")
            sys.exit(1)
        create_test_file(args.module, args.class_name)
    elif args.command == "tdd":
        if not args.test:
            print("错误: 需要 --test 参数")
            sys.exit(1)
        tdd_cycle(args.module, args.test)


if __name__ == "__main__":
    main()
