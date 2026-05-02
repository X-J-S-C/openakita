"""
OpenAkita 架构模块

六边形架构实现，支持模块化、可扩展的 Agent 系统。
"""

from __future__ import annotations

from .kernel import (
    AgentKernel,
    AgentFactory,
    AgentStatus,
    AgentEvent,
    Task,
    KernelConfig,
    CheckpointData,
)

from .context import (
    KernelContext,
    KernelResult,
    StepResult,
    Reflection,
    ExecutionTrace,
    IterationTrace,
    ToolCallTrace,
    PlanPort,
    Plan,
    PlanStep,
    StepStatus,
    PlanEvaluation,
    Skill,
    SkillResult,
    SkillInstallResult,
    SkillPort,
    EvalPort,
    TestCase,
    TestSuite,
    EvalResult,
    BenchmarkResult,
)

from .feature_flags import (
    FeatureFlags,
    FeatureGate,
    FeatureGroup,
    FeatureFlag,
    RolloutManager,
    get_rollout_manager,
)

__version__ = "1.0.0"

__all__ = [
    # 内核
    "AgentKernel",
    "AgentFactory",
    "AgentStatus",
    "AgentEvent",
    "Task",
    "KernelConfig",
    "CheckpointData",
    # 上下文
    "KernelContext",
    "KernelResult",
    "StepResult",
    "Reflection",
    "ExecutionTrace",
    "IterationTrace",
    "ToolCallTrace",
    "PlanPort",
    "Plan",
    "PlanStep",
    "StepStatus",
    "PlanEvaluation",
    # 技能
    "SkillPort",
    "Skill",
    "SkillResult",
    "SkillInstallResult",
    # 评测
    "EvalPort",
    "TestCase",
    "TestSuite",
    "EvalResult",
    "BenchmarkResult",
    # 特性开关
    "FeatureFlags",
    "FeatureGate",
    "FeatureGroup",
    "FeatureFlag",
    "RolloutManager",
    "get_rollout_manager",
]
