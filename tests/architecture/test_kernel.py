"""
AgentKernel TDD 测试

遵循 TDD 流程：Red-Green-Refactor
测试 Agent 内核的核心功能。
"""

from __future__ import annotations

import pytest

from openakita.architecture import (
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
from openakita.architecture.plan import Plan, PlanStep, StepStatus


class MockKernel(AgentKernel):
    """用于测试的 Mock Kernel"""

    def __init__(self):
        super().__init__("mock-kernel")
        self._initialize_called = False
        self._run_called = False
        self._shutdown_called = False
        self._checkpoints: list[CheckpointData] = []

    async def initialize(self) -> None:
        self._initialize_called = True

    async def run(self, task: Task, context: KernelContext) -> KernelResult:
        self._run_called = True
        self._set_status(AgentStatus.COMPLETED)
        return KernelResult(success=True, content="Mock result", iterations=1)

    async def plan(self, goal: str, context: KernelContext) -> Plan:
        return Plan(
            id="mock-plan",
            goal=goal,
            steps=[PlanStep(id="step-1", description=goal, action="execute")],
        )

    async def execute_step(self, step: PlanStep, context: KernelContext) -> StepResult:
        step.complete("Mock step result")
        return StepResult(
            step=step,
            success=True,
            output="Mock step result",
            execution_time_ms=10.0,
        )

    async def reflect(self, result: StepResult, context: KernelContext) -> Reflection:
        return Reflection(
            result=result,
            quality_score=0.8,
            issues=[],
            improvements=[],
        )

    async def checkpoint(self) -> CheckpointData:
        checkpoint = CheckpointData(
            kernel_name=self.name,
            status=self.status.value,
            task_id="",
            iteration=0,
            state_snapshot={},
        )
        self._checkpoints.append(checkpoint)
        return checkpoint

    async def restore(self, checkpoint: CheckpointData) -> None:
        pass

    async def shutdown(self) -> None:
        self._shutdown_called = True


class TestAgentKernelBasics:
    """AgentKernel 基础功能测试"""

    def test_kernel_has_name(self):
        """Kernel 有名称"""
        kernel = MockKernel()
        assert kernel.name == "mock-kernel"

    def test_kernel_starts_with_idle_status(self):
        """Kernel 初始状态为 IDLE"""
        kernel = MockKernel()
        assert kernel.status == AgentStatus.IDLE

    def test_kernel_can_register_event_handler(self):
        """可以注册事件处理器"""
        kernel = MockKernel()
        events = []

        def handler(event):
            events.append(event)

        kernel.on_event("test_event", handler)
        kernel._emit_event(AgentEvent(type="test_event"))

        assert len(events) == 1


class TestAgentKernelLifecycle:
    """AgentKernel 生命周期测试"""

    @pytest.mark.asyncio
    async def test_initialize_sets_initialized_flag(self):
        """初始化设置标志"""
        kernel = MockKernel()
        assert kernel._initialized is False

        await kernel.initialize()
        assert kernel._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_is_idempotent(self):
        """初始化是幂等的"""
        kernel = MockKernel()
        await kernel.initialize()
        await kernel.initialize()

        assert kernel._initialize_called is True

    @pytest.mark.asyncio
    async def test_shutdown_sets_status_to_idle(self):
        """关闭设置状态为 IDLE"""
        kernel = MockKernel()
        await kernel.initialize()
        await kernel.shutdown()

        assert kernel.status == AgentStatus.IDLE


class TestAgentKernelExecution:
    """AgentKernel 执行测试"""

    @pytest.mark.asyncio
    async def test_run_returns_result(self):
        """run 返回结果"""
        kernel = MockKernel()
        await kernel.initialize()

        task = Task(id="test-1", description="测试任务")
        context = KernelContext()

        result = await kernel.run(task, context)

        assert isinstance(result, KernelResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_run_changes_status(self):
        """run 改变状态"""
        kernel = MockKernel()
        await kernel.initialize()

        task = Task(id="test-2", description="测试任务")
        context = KernelContext()

        await kernel.run(task, context)

        assert kernel.status == AgentStatus.COMPLETED


class TestTask:
    """Task 测试"""

    def test_task_has_required_fields(self):
        """Task 有必需字段"""
        task = Task(id="task-1", description="测试")
        assert task.id == "task-1"
        assert task.description == "测试"

    def test_task_is_valid_with_description(self):
        """有描述的任务是有效的"""
        task = Task(id="task-1", description="测试")
        assert task.is_valid is True

    def test_task_is_invalid_without_description(self):
        """无描述的任务是无效的"""
        task = Task(id="task-1", description="")
        assert task.is_valid is False

    def test_task_can_set_priority(self):
        """Task 可以设置优先级"""
        task = Task(id="task-1", description="测试", priority=5)
        assert task.priority == 5


class TestKernelResult:
    """KernelResult 测试"""

    def test_result_is_success(self):
        """成功的 Result"""
        result = KernelResult(success=True, content="测试")
        assert result.is_success is True
        assert result.is_failure is False

    def test_result_is_failure(self):
        """失败的 Result"""
        result = KernelResult(success=False, error="错误")
        assert result.is_success is False
        assert result.is_failure is True


class TestCheckpointData:
    """检查点数据测试"""

    def test_checkpoint_has_required_fields(self):
        """检查点有必需字段"""
        checkpoint = CheckpointData(
            kernel_name="test",
            status="idle",
            task_id="task-1",
            iteration=0,
            state_snapshot={},
        )
        assert checkpoint.kernel_name == "test"
        assert checkpoint.status == "idle"


class TestAgentFactory:
    """AgentFactory 测试"""

    def test_register_and_create_kernel(self):
        """注册并创建 Kernel"""
        class CustomKernel(AgentKernel):
            async def initialize(self) -> None:
                pass

            async def run(self, task: Task, context: KernelContext) -> KernelResult:
                return KernelResult(success=True)

            async def plan(self, goal: str, context: KernelContext) -> Plan:
                return Plan(id="p", goal=goal)

            async def execute_step(self, step: PlanStep, context: KernelContext) -> StepResult:
                return StepResult(step=step, success=True)

            async def reflect(self, result: StepResult, context: KernelContext) -> Reflection:
                return Reflection(result=result, quality_score=1.0)

            async def checkpoint(self) -> CheckpointData:
                return CheckpointData(kernel_name="", status="", task_id="", iteration=0, state_snapshot={})

            async def restore(self, checkpoint: CheckpointData) -> None:
                pass

            async def shutdown(self) -> None:
                pass

        AgentFactory.register("custom", CustomKernel)
        kernel = AgentFactory.create("custom")
        assert isinstance(kernel, CustomKernel)

    def test_create_requires_registered_kernel(self):
        """创建需要注册的 Kernel"""
        with pytest.raises(ValueError):
            AgentFactory.create("nonexistent")

    def test_list_registered_returns_names(self):
        """列出已注册名称"""
        names = AgentFactory.list_registered()
        assert isinstance(names, list)


class TestAgentEvent:
    """AgentEvent 测试"""

    def test_event_has_type_and_timestamp(self):
        """事件有类型和时间戳"""
        event = AgentEvent(type="test")
        assert event.type == "test"
        assert event.timestamp is not None

    def test_event_can_have_data(self):
        """事件可以有数据"""
        event = AgentEvent(type="test", data={"key": "value"})
        assert event.data["key"] == "value"


class TestKernelConfig:
    """KernelConfig 测试"""

    def test_config_has_defaults(self):
        """配置有默认值"""
        config = KernelConfig()
        assert config.max_iterations == 100
        assert config.enable_reflection is True

    def test_config_can_override_defaults(self):
        """配置可以覆盖默认值"""
        config = KernelConfig(max_iterations=50, enable_reflection=False)
        assert config.max_iterations == 50
        assert config.enable_reflection is False


class TestStepResult:
    """StepResult 测试"""

    def test_step_result_success(self):
        """成功的步骤结果"""
        step = PlanStep(id="s1", description="test", action="do")
        result = StepResult(
            step=step,
            success=True,
            output="result",
            execution_time_ms=100.0,
        )
        assert result.success is True
        assert result.output == "result"

    def test_step_result_failure(self):
        """失败的步骤结果"""
        step = PlanStep(id="s1", description="test", action="do")
        result = StepResult(
            step=step,
            success=False,
            error="Error occurred",
        )
        assert result.success is False
        assert result.error == "Error occurred"


class TestReflection:
    """Reflection 测试"""

    def test_reflection_should_retry(self):
        """反思决定是否重试"""
        step = PlanStep(id="s1", description="test", action="do")
        result = StepResult(step=step, success=False)
        reflection = Reflection(
            result=result,
            quality_score=0.3,
            issues=["Issue 1"],
            should_retry=True,
        )
        assert reflection.should_retry is True

    def test_reflection_no_retry_on_success(self):
        """成功时不重试"""
        step = PlanStep(id="s1", description="test", action="do")
        result = StepResult(step=step, success=True)
        reflection = Reflection(
            result=result,
            quality_score=0.9,
            issues=[],
            should_retry=False,
        )
        assert reflection.should_retry is False
