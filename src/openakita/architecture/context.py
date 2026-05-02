"""
上下文与结果定义

提供内核执行所需的上下文和结果类型。
"""

from __future__ import annotations

import logging
from enum import Enum

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .ports.memory import MemoryPort
    from .ports.tools import ToolPort, ToolContext
    from .ports.model import ModelPort
    from .ports.skills import SkillPort

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class KernelContext:
    """内核执行上下文"""
    memory: MemoryPort | None = None
    tools: ToolPort | None = None
    model: ModelPort | None = None
    skills: SkillPort | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        self.metadata[key] = value

    def to_tool_context(self) -> "ToolContext":
        """转换为工具上下文"""
        from .ports.tools import ToolContext
        return ToolContext(
            session_id=self.get_metadata("session_id", ""),
            agent_id=self.get_metadata("agent_id", ""),
            user_id=self.get_metadata("user_id", ""),
            cwd=self.get_metadata("cwd", ""),
            env=self.get_metadata("env", {}),
            metadata=self.metadata,
        )

    def with_memory(self, memory: "MemoryPort") -> "KernelContext":
        """设置记忆端口"""
        return KernelContext(
            memory=memory,
            tools=self.tools,
            model=self.model,
            skills=self.skills,
            metadata=self.metadata.copy(),
        )

    def with_tools(self, tools: "ToolPort") -> "KernelContext":
        """设置工具端口"""
        return KernelContext(
            memory=self.memory,
            tools=tools,
            model=self.model,
            skills=self.skills,
            metadata=self.metadata.copy(),
        )

    def with_model(self, model: "ModelPort") -> "KernelContext":
        """设置模型端口"""
        return KernelContext(
            memory=self.memory,
            tools=self.tools,
            model=model,
            skills=self.skills,
            metadata=self.metadata.copy(),
        )


@dataclass
class KernelResult:
    """内核执行结果"""
    success: bool
    content: str = ""
    error: str | None = None
    iterations: int = 0
    duration_ms: float = 0.0
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    memory_updates: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.success

    @property
    def is_failure(self) -> bool:
        return not self.success


@dataclass
class StepResult:
    """步骤执行结果"""
    step: "PlanStep" = None
    success: bool = False
    output: Any = None
    error: str | None = None
    tool_results: list[Any] = field(default_factory=list)
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Reflection:
    """反思结果"""
    result: StepResult = None
    quality_score: float = 0.0
    issues: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    should_retry: bool = False
    next_steps: list[str] = field(default_factory=list)


@dataclass
class ExecutionTrace:
    """执行追踪"""
    task_id: str
    kernel_name: str
    iterations: list[IterationTrace] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    total_duration_ms: float = 0.0

    def add_iteration(self, iteration: "IterationTrace") -> None:
        """添加迭代追踪"""
        self.iterations.append(iteration)

    def complete(self) -> None:
        """标记完成"""
        self.end_time = datetime.now()
        self.total_duration_ms = sum(i.duration_ms for i in self.iterations)


@dataclass
class IterationTrace:
    """迭代追踪"""
    iteration: int
    step: str
    action: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    duration_ms: float = 0.0
    tool_calls: list[ToolCallTrace] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_tool_call(self, tool_call: "ToolCallTrace") -> None:
        """添加工具调用追踪"""
        self.tool_calls.append(tool_call)

    def add_error(self, error: str) -> None:
        """添加错误"""
        self.errors.append(error)

    def complete(self) -> None:
        """标记完成"""
        self.end_time = datetime.now()
        if self.end_time:
            self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000


@dataclass
class ToolCallTrace:
    """工具调用追踪"""
    tool_name: str
    arguments: dict[str, Any]
    result: str = ""
    success: bool = True
    duration_ms: float = 0.0
    error: str | None = None


class PlanPort(ABC):
    """
    规划端口

    定义任务规划的核心接口。
    """

    @abstractmethod
    async def plan(
        self,
        goal: str,
        context: KernelContext,
    ) -> "Plan":
        """
        生成执行计划

        Args:
            goal: 目标描述
            context: 规划上下文

        Returns:
            执行计划
        """
        pass

    @abstractmethod
    async def replan(
        self,
        original_plan: "Plan",
        feedback: str,
        context: KernelContext,
    ) -> "Plan":
        """
        根据反馈重新规划

        Args:
            original_plan: 原计划
            feedback: 反馈信息
            context: 规划上下文

        Returns:
            新计划
        """
        pass

    @abstractmethod
    async def evaluate(
        self,
        plan: "Plan",
        context: KernelContext,
    ) -> "PlanEvaluation":
        """
        评估计划质量

        Args:
            plan: 计划
            context: 评估上下文

        Returns:
            评估结果
        """
        pass


@dataclass
class Plan:
    """执行计划"""
    id: str
    goal: str
    steps: list["PlanStep"] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: "PlanStep") -> None:
        """添加步骤"""
        self.steps.append(step)

    def get_step(self, step_id: str) -> "PlanStep | None":
        """获取步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    @property
    def is_complete(self) -> bool:
        return len(self.steps) > 0 and all(s.status == StepStatus.COMPLETED for s in self.steps)

    @property
    def progress(self) -> float:
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)
        return completed / len(self.steps)


@dataclass
class PlanStep:
    """计划步骤"""
    id: str
    description: str
    action: str
    status: "StepStatus" = field(default_factory="StepStatus.PENDING")
    result: Any = None
    error: str | None = None
    dependencies: list[str] = field(default_factory=list)
    estimated_duration_ms: float = 0.0
    actual_duration_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        """开始步骤"""
        self.status = StepStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete(self, result: Any = None) -> None:
        """完成步骤"""
        self.status = StepStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
        if self.started_at:
            self.actual_duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000

    def fail(self, error: str) -> None:
        """步骤失败"""
        self.status = StepStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error

    def skip(self) -> None:
        """跳过步骤"""
        self.status = StepStatus.SKIPPED
        self.completed_at = datetime.now()


class PlanEvaluation:
    """计划评估"""
    plan: Plan
    quality_score: float  # 0-1
    feasibility_score: float  # 0-1
    efficiency_score: float  # 0-1
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    estimated_total_duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class SkillPort(ABC):
    """
    Skills 端口

    定义技能系统的核心接口。
    """

    @abstractmethod
    async def list_skills(
        self,
        context: KernelContext,
    ) -> list["Skill"]:
        """
        列出可用技能

        Args:
            context: 列表上下文

        Returns:
            技能列表
        """
        pass

    @abstractmethod
    async def execute_skill(
        self,
        skill_id: str,
        arguments: dict[str, Any],
        context: KernelContext,
    ) -> "SkillResult":
        """
        执行技能

        Args:
            skill_id: 技能 ID
            arguments: 技能参数
            context: 执行上下文

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    async def install_skill(
        self,
        skill_source: str,
        context: KernelContext,
    ) -> "SkillInstallResult":
        """
        安装技能

        Args:
            skill_source: 技能源（URL、文件路径等）
            context: 安装上下文

        Returns:
            安装结果
        """
        pass

    @abstractmethod
    async def uninstall_skill(
        self,
        skill_id: str,
        context: KernelContext,
    ) -> bool:
        """
        卸载技能

        Args:
            skill_id: 技能 ID
            context: 卸载上下文

        Returns:
            是否成功
        """
        pass


@dataclass
class Skill:
    """技能定义"""
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    source: str = ""
    is_builtin: bool = False
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillResult:
    """技能执行结果"""
    skill_id: str
    success: bool
    output: str = ""
    error: str | None = None
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillInstallResult:
    """技能安装结果"""
    success: bool
    skill: Skill | None = None
    error: str | None = None
    installed_files: list[str] = field(default_factory=list)


class EvalPort(ABC):
    """
    评测端口

    定义 Agent 评测的核心接口。
    """

    @abstractmethod
    async def evaluate(
        self,
        agent: Any,
        test_case: "TestCase",
        context: KernelContext,
    ) -> "EvalResult":
        """
        评测 Agent

        Args:
            agent: 待评测 Agent
            test_case: 测试用例
            context: 评测上下文

        Returns:
            评测结果
        """
        pass

    @abstractmethod
    async def benchmark(
        self,
        agent: Any,
        test_suite: "TestSuite",
        context: KernelContext,
    ) -> "BenchmarkResult":
        """
        运行基准测试

        Args:
            agent: 待评测 Agent
            test_suite: 测试套件
            context: 评测上下文

        Returns:
            基准测试结果
        """
        pass


@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    description: str
    input: str
    expected_output: str | None = None
    evaluation_criteria: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuite:
    """测试套件"""
    id: str
    name: str
    description: str
    test_cases: list[TestCase] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalResult:
    """评测结果"""
    test_case_id: str
    success: bool
    score: float = 0.0
    output: str = ""
    error: str | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    suite_id: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    overall_score: float = 0.0
    results: list[EvalResult] = field(default_factory=list)
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return self.passed / self.total_tests
