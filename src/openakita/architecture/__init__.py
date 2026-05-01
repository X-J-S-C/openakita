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
    KernelContext,
    KernelResult,
    StepResult,
    Reflection,
    CheckpointData,
)

from .feature_flags import (
    FeatureFlags,
    FeatureGate,
    FeatureGroup,
    FeatureFlag,
    RolloutManager,
    get_rollout_manager,
)

from .context import (
    KernelContext,
    KernelResult,
    ExecutionTrace,
    IterationTrace,
    ToolCallTrace,
    PlanPort,
    Plan,
    PlanStep,
    StepStatus,
    PlanEvaluation,
    SkillPort,
    Skill,
    SkillResult,
    SkillInstallResult,
    EvalPort,
    TestCase,
    TestSuite,
    EvalResult,
    BenchmarkResult,
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
    "KernelContext",
    "KernelResult",
    "StepResult",
    "Reflection",
    "CheckpointData",
    # 特性开关
    "FeatureFlags",
    "FeatureGate",
    "FeatureGroup",
    "FeatureFlag",
    "RolloutManager",
    "get_rollout_manager",
    # 上下文
    "ExecutionTrace",
    "IterationTrace",
    "ToolCallTrace",
    "PlanPort",
    "Plan",
    "PlanStep",
    "StepStatus",
    "PlanEvaluation",
    "SkillPort",
    "Skill",
    "SkillResult",
    "SkillInstallResult",
    "EvalPort",
    "TestCase",
    "TestSuite",
    "EvalResult",
    "BenchmarkResult",
]
