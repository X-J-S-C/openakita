"""
FeatureFlags TDD 测试

遵循 TDD 流程：Red-Green-Refactor
1. 先写失败的测试 (RED)
2. 实现代码使其通过 (GREEN)
3. 重构代码 (REFACTOR)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

SRC_PATH = str(Path(__file__).resolve().parent.parent.parent / "src")
sys.path.insert(0, SRC_PATH)

import pytest

from openakita.architecture.feature_flags import (
    FeatureFlags,
    FeatureGate,
    FeatureGroup,
    FeatureFlag,
    FeatureDisabledError,
    RolloutManager,
    get_rollout_manager,
)


class TestFeatureFlagsBasics:
    """FeatureFlags 基础功能测试"""

    def test_is_enabled_returns_default_when_not_set(self):
        """当开关未设置时，返回默认值"""
        result = FeatureFlags.is_enabled("nonexistent.flag", default=True)
        assert result is True

        result = FeatureFlags.is_enabled("nonexistent.flag", default=False)
        assert result is False

    def test_is_enabled_respects_env_variable(self, monkeypatch):
        """环境变量可以覆盖开关状态"""
        monkeypatch.setenv("AKITA_FLAG_TEST_FLAG", "true")
        result = FeatureFlags.is_enabled("test.flag")
        assert result is True

        monkeypatch.setenv("AKITA_FLAG_TEST_FLAG", "false")
        result = FeatureFlags.is_enabled("test.flag")
        assert result is False

    def test_is_enabled_handles_various_env_values(self, monkeypatch):
        """测试各种环境变量值"""
        for true_value in ["true", "True", "TRUE", "1", "yes", "on"]:
            monkeypatch.setenv("AKITA_FLAG_TEST_FLAG", true_value)
            assert FeatureFlags.is_enabled("test.flag") is True

        for false_value in ["false", "False", "FALSE", "0", "no", "off", ""]:
            monkeypatch.setenv("AKITA_FLAG_TEST_FLAG", false_value)
            assert FeatureFlags.is_enabled("test.flag") is False

    def test_enable_temporarily_sets_flag(self):
        """临时启用开关"""
        FeatureFlags.enable("temp.test", temporary=True)
        assert FeatureFlags.is_enabled("temp.test", default=False) is True

    def test_disable_temporarily_sets_flag(self):
        """临时禁用开关"""
        FeatureFlags.disable("temp.test", temporary=True)
        assert FeatureFlags.is_enabled("temp.test", default=True) is False

    def test_enable_permanently_sets_flag(self):
        """永久启用开关会修改默认值"""
        FeatureFlags.enable("permanent.test", temporary=False)
        assert FeatureFlags.is_enabled("permanent.test") is True

    def test_disable_permanently_sets_flag(self):
        """永久禁用开关会修改默认值"""
        FeatureFlags.disable("permanent.off", temporary=False)
        assert FeatureFlags.is_enabled("permanent.off", default=True) is False

    def test_clear_override_removes_override(self, monkeypatch):
        """清除覆盖恢复默认值"""
        monkeypatch.setenv("AKITA_FLAG_CLEAR_TEST", "true")
        assert FeatureFlags.is_enabled("clear.test") is True

        FeatureFlags.clear_override("clear.test")
        assert FeatureFlags.is_enabled("clear.test") is False


class TestFeatureFlagRegistration:
    """特性开关注册测试"""

    def test_register_flag_adds_to_registry(self):
        """注册新开关"""
        flag = FeatureFlag(
            name="custom.flag",
            description="自定义开关",
            group=FeatureGroup.KERNEL,
            default_value=True,
        )
        FeatureFlags.register_flag(flag)

        info = FeatureFlags.get_flag_info("custom.flag")
        assert info["name"] == "custom.flag"
        assert info["enabled"] is True

    def test_get_flag_info_returns_dict(self):
        """获取开关信息返回字典"""
        info = FeatureFlags.get_flag_info("openakita.kernel.v2")
        assert isinstance(info, dict)
        assert "name" in info
        assert "description" in info
        assert "group" in info

    def test_get_flag_info_returns_empty_for_nonexistent(self):
        """不存在的开关返回空字典"""
        info = FeatureFlags.get_flag_info("nonexistent.flag")
        assert info == {}

    def test_list_flags_returns_all_flags(self):
        """列出所有开关"""
        flags = FeatureFlags.list_flags()
        assert isinstance(flags, list)
        assert len(flags) > 0

    def test_list_flags_filters_by_group(self):
        """按分组列出开关"""
        kernel_flags = FeatureFlags.list_flags(FeatureGroup.KERNEL)
        assert all(f["group"] == "kernel" for f in kernel_flags)


class TestFeatureGateDecorator:
    """FeatureGate 装饰器测试"""

    def test_feature_gate_calls_function_when_enabled(self, monkeypatch):
        """开关启用时调用函数"""
        monkeypatch.setenv("AKITA_FLAG_GATE_TEST", "true")

        gate = FeatureGate("gate.test", default=False)

        @gate
        def test_function():
            return "executed"

        result = test_function()
        assert result == "executed"

    def test_feature_gate_raises_when_disabled(self, monkeypatch):
        """开关禁用时抛出异常"""
        monkeypatch.setenv("AKITA_FLAG_GATE_TEST", "false")

        gate = FeatureGate("gate.test", default=False)

        @gate
        def test_function():
            return "executed"

        with pytest.raises(FeatureDisabledError) as exc_info:
            test_function()
        assert exc_info.value.flag_name == "gate.test"

    def test_feature_gate_calls_fallback_when_disabled(self, monkeypatch):
        """开关禁用时调用 fallback"""
        monkeypatch.setenv("AKITA_FLAG_GATE_TEST", "false")

        gate = FeatureGate("gate.test", default=False, fallback=lambda: "fallback")

        @gate
        def test_function():
            return "executed"

        result = test_function()
        assert result == "fallback"


class TestRolloutManager:
    """灰度发布管理器测试"""

    def test_create_experiment(self):
        """创建灰度实验"""
        manager = get_rollout_manager()
        experiment = manager.create_experiment(
            experiment_id="exp-1",
            flag_name="test.flag",
            description="测试实验",
            target_percentage=50.0,
        )

        assert experiment.id == "exp-1"
        assert experiment.flag_name == "test.flag"
        assert experiment.target_percentage == 50.0
        assert experiment.completed is False

    def test_update_experiment_percentage(self):
        """更新实验灰度百分比"""
        manager = get_rollout_manager()
        manager.create_experiment(
            experiment_id="exp-2",
            flag_name="test.flag",
            description="测试实验",
            target_percentage=100.0,
        )

        manager.update_experiment("exp-2", 75.0)

        status = manager.get_experiment_status("exp-2")
        assert status["current_percentage"] == 75.0

    def test_complete_experiment_success(self):
        """实验成功完成"""
        manager = get_rollout_manager()
        manager.create_experiment(
            experiment_id="exp-3",
            flag_name="test.success.flag",
            description="成功实验",
            target_percentage=100.0,
        )

        manager.complete_experiment("exp-3", success=True)

        status = manager.get_experiment_status("exp-3")
        assert status["completed"] is True
        assert status["success"] is True

    def test_complete_experiment_failure(self):
        """实验失败完成"""
        manager = get_rollout_manager()
        manager.create_experiment(
            experiment_id="exp-4",
            flag_name="test.fail.flag",
            description="失败实验",
            target_percentage=100.0,
        )

        manager.complete_experiment("exp-4", success=False)

        status = manager.get_experiment_status("exp-4")
        assert status["completed"] is True
        assert status["success"] is False

    def test_record_metric(self):
        """记录实验指标"""
        manager = get_rollout_manager()
        manager.create_experiment(
            experiment_id="exp-5",
            flag_name="test.metric.flag",
            description="指标实验",
            target_percentage=100.0,
        )

        manager.record_metric("exp-5", "latency_ms", 100.0)
        manager.record_metric("exp-5", "latency_ms", 150.0)

        status = manager.get_experiment_status("exp-5")
        assert "latency_ms" in status["metrics"]
        assert status["metrics"]["latency_ms"]["count"] == 2


class TestGrayScaling:
    """灰度发布测试"""

    def test_gray_scaling_is_deterministic(self):
        """灰度发布是确定性的"""
        results = []
        for _ in range(10):
            result = FeatureFlags.is_enabled(
                "gray.test",
                user_id="user-123",
                default=False,
            )
            results.append(result)

        assert all(r == results[0] for r in results)

    def test_gray_scaling_different_users_different_buckets(self):
        """不同用户在不同的桶中"""
        buckets = set()
        for i in range(100):
            result = FeatureFlags.is_enabled(
                "gray.user.test",
                user_id=f"user-{i}",
                default=False,
            )
            buckets.add(result)

        assert len(buckets) == 2


class TestFeatureDependencies:
    """特性依赖测试"""

    def test_disabled_dependency_disables_flag(self, monkeypatch):
        """禁用的依赖会禁用主开关"""
        monkeypatch.setenv("AKITA_FLAG_PARENT_FLAG", "true")
        monkeypatch.setenv("AKITA_FLAG_CHILD_FLAG", "false")

        parent_flag = FeatureFlag(
            name="parent.flag",
            description="父开关",
            dependencies=["child.flag"],
            default_value=True,
        )
        FeatureFlags.register_flag(parent_flag)

        result = FeatureFlags.is_enabled("parent.flag", default=True)
        assert result is False

    def test_missing_dependency_uses_default(self, monkeypatch):
        """缺失的依赖使用默认值"""
        flag = FeatureFlag(
            name="no.dep.flag",
            description="无依赖开关",
            dependencies=["nonexistent.dep"],
            default_value=True,
        )
        FeatureFlags.register_flag(flag)

        result = FeatureFlags.is_enabled("no.dep.flag", default=True)
        assert result is True
