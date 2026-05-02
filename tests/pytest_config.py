"""
Pytest 配置

为测试提供全局 fixtures 和配置。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture(autouse=True)
def reset_environment():
    """重置环境变量"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def clean_feature_flags():
    """清理特性开关状态"""
    from architecture.feature_flags import FeatureFlags
    FeatureFlags._overrides.clear()
    FeatureFlags._user_overrides.clear()
    yield


@pytest.fixture
def temp_data_dir(tmp_path):
    """临时数据目录"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_kernel_config():
    """示例内核配置"""
    from architecture import KernelConfig
    return KernelConfig(
        max_iterations=10,
        enable_reflection=True,
        enable_self_correction=True,
    )


def pytest_configure(config):
    """Pytest 配置钩子"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "contract: Contract tests")


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    for item in items:
        if "architecture" in str(item.fspath):
            item.add_marker(pytest.mark.unit)


def pytest_report_header(config):
    """测试报告头"""
    return [
        "OpenAkita Architecture TDD Tests",
        "=" * 50,
    ]
