"""
Agent 核心内核 - 六边形架构核心

提供 Agent 执行的核心抽象，与外部适配器解耦。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from .context import KernelContext
    from .ports.memory import MemoryPort
    from .ports.tools import ToolPort, ToolCall
    from .ports.model import ModelPort
    from .ports.skills import SkillPort

logger = logging.getLogger(__name__)

TState = TypeVar("TState", bound=Enum)


class AgentStatus(Enum):
    """Agent 执行状态"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_TOOL = "waiting_tool"
    WAITING_USER = "waiting_user"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentEvent:
    """Agent 事件"""
    type: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)


class StateMachine(ABC, Generic[TState]):
    """状态机抽象"""

    @property
    @abstractmethod
    def current_state(self) -> TState:
        """获取当前状态"""
        pass

    @abstractmethod
    async def transition(self, event: AgentEvent) -> TState:
        """状态转换"""
        pass

    @abstractmethod
    def can_transition(self, event: AgentEvent) -> bool:
        """检查是否可以转换"""
        pass


@dataclass
class KernelConfig:
    """内核配置"""
    max_iterations: int = 100
    max_planning_time_seconds: float = 30.0
    checkpoint_interval: int = 10
    enable_reflection: bool = True
    enable_self_correction: bool = True
    tool_timeout_seconds: float = 60.0
    user_confirm_threshold: float = 0.8


@dataclass
class Task:
    """任务定义"""
    id: str
    description: str
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    priority: int = 0

    @property
    def is_valid(self) -> bool:
        return bool(self.description.strip())


@dataclass
class CheckpointData:
    """检查点数据"""
    kernel_name: str
    status: str
    task_id: str
    iteration: int
    state_snapshot: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    version: str = "1.0"


class AgentKernel(ABC):
    """
    Agent 执行内核 - 六边形架构核心

    职责:
    - 管理 Agent 生命周期
    - 协调规划、执行、反思
    - 状态持久化
    - 事件驱动架构
    """

    def __init__(
        self,
        name: str,
        config: KernelConfig | None = None,
    ):
        self.name = name
        self.config = config or KernelConfig()
        self._status = AgentStatus.IDLE
        self._event_handlers: dict[str, list[callable]] = {}
        self._initialized = False
        self._memory_port: "MemoryPort | None" = None
        self._tool_port: "ToolPort | None" = None
        self._model_port: "ModelPort | None" = None
        self._skill_port: "SkillPort | None" = None

    @property
    def status(self) -> AgentStatus:
        """获取当前状态"""
        return self._status

    def _set_status(self, status: AgentStatus) -> None:
        """设置状态并触发事件"""
        old_status = self._status
        self._status = status
        self._emit_event(AgentEvent(
            type="status_changed",
            data={"old": old_status.value, "new": status.value}
        ))

    @abstractmethod
    async def initialize(self) -> None:
        """初始化内核"""
        pass

    @abstractmethod
    async def run(self, task: Task, context: "KernelContext") -> "KernelResult":
        """
        执行任务的主入口

        Args:
            task: 要执行的任务
            context: 执行上下文

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    async def plan(self, goal: str, context: "KernelContext") -> "Plan":
        """
        任务规划

        Args:
            goal: 目标描述
            context: 规划上下文

        Returns:
            执行计划
        """
        pass

    @abstractmethod
    async def execute_step(self, step: "PlanStep", context: "KernelContext") -> "StepResult":
        """
        执行单个步骤

        Args:
            step: 计划步骤
            context: 执行上下文

        Returns:
            步骤执行结果
        """
        pass

    @abstractmethod
    async def reflect(self, result: "StepResult", context: "KernelContext") -> "Reflection":
        """
        反思执行结果

        Args:
            result: 执行结果
            context: 反思上下文

        Returns:
            反思结果
        """
        pass

    @abstractmethod
    async def checkpoint(self) -> CheckpointData:
        """
        创建检查点

        用于崩溃恢复和状态持久化。
        """
        pass

    @abstractmethod
    async def restore(self, checkpoint: CheckpointData) -> None:
        """
        从检查点恢复

        Args:
            checkpoint: 检查点数据
        """
        pass

    def on_event(self, event_type: str, handler: callable) -> None:
        """注册事件处理器"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def _emit_event(self, event: AgentEvent) -> None:
        """触发事件"""
        handlers = self._event_handlers.get(event.type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.warning(f"Event handler error: {e}")

    @abstractmethod
    async def shutdown(self) -> None:
        """优雅关闭"""
        pass


class KernelPort(ABC):
    """
    内核端口 - 用于测试和模拟

    定义内核必须实现的核心接口。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def status(self) -> AgentStatus:
        pass

    @abstractmethod
    async def run(self, task: Task, context: "KernelContext") -> "KernelResult":
        pass

    @abstractmethod
    async def checkpoint(self) -> CheckpointData:
        pass


class AgentFactory:
    """Agent 实例工厂"""

    _registry: dict[str, type[AgentKernel]] = {}
    _default: str | None = None

    @classmethod
    def register(
        cls,
        name: str,
        kernel_class: type[AgentKernel],
        set_default: bool = False,
    ) -> None:
        """注册 Agent 内核"""
        cls._registry[name] = kernel_class
        if set_default or not cls._default:
            cls._default = name

    @classmethod
    def create(cls, name: str | None = None, **kwargs) -> AgentKernel:
        """创建 Agent 实例"""
        kernel_name = name or cls._default
        if not kernel_name:
            raise ValueError("No agent kernel registered")
        kernel_class = cls._registry.get(kernel_name)
        if not kernel_class:
            raise ValueError(f"Unknown agent kernel: {kernel_name}")
        return kernel_class(**kwargs)

    @classmethod
    def list_registered(cls) -> list[str]:
        """列出已注册的 Agent"""
        return list(cls._registry.keys())


class KernelContextBuilder:
    """内核上下文构建器"""

    def __init__(self):
        self._memory_port: "MemoryPort | None" = None
        self._tool_port: "ToolPort | None" = None
        self._model_port: "ModelPort | None" = None
        self._skill_port: "SkillPort | None" = None
        self._metadata: dict[str, Any] = {}

    def with_memory(self, port: "MemoryPort") -> "KernelContextBuilder":
        self._memory_port = port
        return self

    def with_tools(self, port: "ToolPort") -> "KernelContextBuilder":
        self._tool_port = port
        return self

    def with_model(self, port: "ModelPort") -> "KernelContextBuilder":
        self._model_port = port
        return self

    def with_skills(self, port: "SkillPort") -> "KernelContextBuilder":
        self._skill_port = port
        return self

    def with_metadata(self, key: str, value: Any) -> "KernelContextBuilder":
        self._metadata[key] = value
        return self

    def build(self) -> "KernelContext":
        from .context import KernelContext
        return KernelContext(
            memory=self._memory_port,
            tools=self._tool_port,
            model=self._model_port,
            skills=self._skill_port,
            metadata=self._metadata,
        )


AgentFactory.register("ralph", None)


class RalphKernel(AgentKernel):
    """
    Ralph Wiggum 风格的内核实现

    核心特性:
    - 永不放弃的循环
    - 状态持久化到文件
    - 每次迭代 fresh context
    - 自我反思与修正
    """

    async def initialize(self) -> None:
        if self._initialized:
            return

        logger.info(f"[RalphKernel] Initializing {self.name}")
        self._initialized = True

    async def run(self, task: Task, context: "KernelContext") -> "KernelResult":
        """执行 Ralph 循环"""
        from .context import KernelResult

        if not self._initialized:
            await self.initialize()

        self._set_status(AgentStatus.PLANNING)

        plan = await self.plan(task.description, context)

        self._set_status(AgentStatus.EXECUTING)

        for iteration, step in enumerate(plan.steps):
            self._emit_event(AgentEvent(
                type="iteration_start",
                data={"iteration": iteration, "step": step.description}
            ))

            result = await self.execute_step(step, context)

            if self.config.enable_reflection:
                self._set_status(AgentStatus.REFLECTING)
                reflection = await self.reflect(result, context)

                if reflection.should_retry and iteration < self.config.max_iterations:
                    logger.info(f"[RalphKernel] Retrying step due to: {reflection.issues}")
                    continue

            if not result.success and not self.config.enable_self_correction:
                self._set_status(AgentStatus.FAILED)
                return KernelResult(
                    success=False,
                    error=result.error,
                    iterations=iteration + 1,
                )

            self._emit_event(AgentEvent(
                type="iteration_complete",
                data={"iteration": iteration, "success": result.success}
            ))

            if iteration % self.config.checkpoint_interval == 0:
                await self.checkpoint()

        self._set_status(AgentStatus.COMPLETED)
        return KernelResult(success=True, iterations=len(plan.steps))

    async def plan(self, goal: str, context: "KernelContext") -> "Plan":
        """生成执行计划"""
        from .context import Plan
        from .plan import PlanStep

        if self._model_port is None:
            return Plan(steps=[PlanStep(id="1", description=goal, action="execute")])

        messages = [
            {"role": "system", "content": "Decompose the task into executable steps."},
            {"role": "user", "content": goal},
        ]

        response = await self._model_port.chat(messages)

        steps = self._parse_plan_response(response.text)
        return Plan(steps=steps)

    def _parse_plan_response(self, response: str) -> list["PlanStep"]:
        """解析计划响应"""
        from .plan import PlanStep

        steps = []
        for i, line in enumerate(response.split("\n"), 1):
            line = line.strip()
            if line and not line.startswith("#"):
                steps.append(PlanStep(
                    id=str(i),
                    description=line,
                    action="execute",
                ))
        return steps if steps else [PlanStep(id="1", description=response, action="execute")]

    async def execute_step(self, step: "PlanStep", context: "KernelContext") -> "StepResult":
        """执行单个步骤"""
        from .context import StepResult
        import time

        start_time = time.time()

        if self._tool_port is None:
            return StepResult(
                step=step,
                success=True,
                output=step.description,
                execution_time_ms=0,
            )

        tool_calls = self._parse_tool_calls(step.action)

        if not tool_calls:
            return StepResult(
                step=step,
                success=True,
                output=step.description,
                execution_time_ms=0,
            )

        tool_results = []
        for tool_call in tool_calls:
            result = await self._tool_port.execute(tool_call, context.to_tool_context())
            tool_results.append(result)

        success = all(r.success for r in tool_results)
        error = tool_results[-1].error if not success else None

        return StepResult(
            step=step,
            success=success,
            output="\n".join(r.output for r in tool_results if r.output),
            error=error,
            tool_results=tool_results,
            execution_time_ms=(time.time() - start_time) * 1000,
        )

    def _parse_tool_calls(self, action: str) -> list["ToolCall"]:
        """解析工具调用"""
        return []

    async def reflect(self, result: "StepResult", context: "KernelContext") -> "Reflection":
        """反思执行结果"""
        from .context import Reflection

        if not result.success:
            return Reflection(
                result=result,
                quality_score=0.0,
                issues=[result.error or "Unknown error"],
                should_retry=True,
            )

        return Reflection(
            result=result,
            quality_score=0.8,
            should_retry=False,
        )

    async def checkpoint(self) -> CheckpointData:
        """创建检查点"""
        return CheckpointData(
            kernel_name=self.name,
            status=self.status.value,
            task_id="",
            iteration=0,
            state_snapshot={},
        )

    async def restore(self, checkpoint: CheckpointData) -> None:
        """从检查点恢复"""
        self._set_status(AgentStatus(checkpoint.status))

    async def shutdown(self) -> None:
        """优雅关闭"""
        logger.info(f"[RalphKernel] Shutting down {self.name}")
        self._set_status(AgentStatus.IDLE)


AgentFactory._registry["ralph"] = RalphKernel
