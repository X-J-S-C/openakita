"""
TDD 测试配置

为架构模块提供 pytest 配置和 fixtures。
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Generator

import pytest

SRC_PATH = str(Path(__file__).resolve().parent.parent.parent / "src")
sys.path.insert(0, SRC_PATH)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "openakita"))

import openakita.architecture as architecture
from openakita.architecture import (
    AgentKernel,
    KernelContext,
    KernelConfig,
    Task,
    AgentStatus,
    AgentEvent,
    KernelResult,
    StepResult,
    Reflection,
    CheckpointData,
)
from openakita.architecture.ports import (
    MemoryPort,
    ToolPort,
    ModelPort,
    SkillPort,
    CollaborationPort,
    Memory,
    MemoryType,
    MemoryPriority,
    MemoryQuery,
    Tool,
    ToolCall,
    ToolResult,
    ToolContext,
    Message,
    MessageRole,
    ModelResponse,
    ModelConfig,
    ModelProvider,
)


class EventCollector:
    """事件收集器，用于测试断言"""

    def __init__(self):
        self.events: list[dict] = []

    def collect(self, event: dict) -> None:
        self.events.append(event)

    def assert_event(self, event_type: str, count: int = 1) -> None:
        matching = [e for e in self.events if e.get("type") == event_type]
        assert len(matching) == count, f"Expected {count} events of type '{event_type}', got {len(matching)}"

    def assert_event_with_data(self, event_type: str, data_key: str, data_value: any) -> None:
        matching = [e for e in self.events if e.get("type") == event_type and e.get("data", {}).get(data_key) == data_value]
        assert len(matching) > 0, f"Expected event '{event_type}' with {data_key}={data_value}"

    def clear(self) -> None:
        self.events.clear()


@pytest.fixture
def event_collector() -> EventCollector:
    """创建事件收集器"""
    return EventCollector()


@pytest.fixture
def kernel_config() -> KernelConfig:
    """创建测试用内核配置"""
    return KernelConfig(
        max_iterations=10,
        max_planning_time_seconds=5.0,
        checkpoint_interval=5,
        enable_reflection=True,
        enable_self_correction=True,
    )


@pytest.fixture
def sample_task() -> Task:
    """创建示例任务"""
    return Task(
        id="test-task-1",
        description="测试任务：计算 1+1",
        priority=1,
    )


@pytest.fixture
def kernel_context() -> KernelContext:
    """创建空的内核上下文"""
    return KernelContext(metadata={"test": True})


@pytest.fixture
def memory_context():
    """创建记忆上下文"""
    from openakita.architecture.ports.memory import StoreContext
    return StoreContext(
        agent_id="test-agent",
        session_id="test-session",
        priority=MemoryPriority.MEDIUM,
    )


@pytest.fixture
def tool_context() -> ToolContext:
    """创建工具上下文"""
    return ToolContext(
        session_id="test-session",
        agent_id="test-agent",
        cwd="/tmp",
        env={},
    )


@pytest.fixture
def sample_memory() -> Memory:
    """创建示例记忆"""
    return Memory(
        id="mem-1",
        content="这是一个测试记忆",
        type=MemoryType.EPISODIC,
        priority=MemoryPriority.MEDIUM,
        importance=0.8,
        agent_id="test-agent",
        session_id="test-session",
        tags=["test", "sample"],
    )


@pytest.fixture
def sample_tool() -> Tool:
    """创建示例工具"""
    return Tool(
        name="test_tool",
        description="测试工具",
        input_schema={
            "type": "object",
            "properties": {
                "input": {"type": "string"},
            },
            "required": ["input"],
        },
        category="general",
    )


@pytest.fixture
def sample_tool_call() -> ToolCall:
    """创建示例工具调用"""
    return ToolCall(
        id="call-1",
        name="test_tool",
        arguments={"input": "test"},
        session_id="test-session",
        agent_id="test-agent",
    )


@pytest.fixture
def sample_messages() -> list[Message]:
    """创建示例消息列表"""
    return [
        Message(role=MessageRole.SYSTEM, content="你是一个测试助手"),
        Message(role=MessageRole.USER, content="你好"),
    ]


@pytest.fixture
def mock_model_config() -> ModelConfig:
    """创建模拟模型配置"""
    return ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model="claude-test",
        max_tokens=100,
        temperature=0.7,
    )


@pytest.fixture
def mock_model_response() -> ModelResponse:
    """创建模拟模型响应"""
    return ModelResponse(
        content="这是模拟响应",
        stop_reason="stop",
        model="claude-test",
    )


@pytest.fixture
def async_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """为异步测试提供事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class AsyncTestHelper:
    """异步测试辅助类"""

    @staticmethod
    async def run_async(coro):
        """运行异步协程"""
        return await coro


@pytest.fixture
def async_helper() -> AsyncTestHelper:
    """异步测试辅助"""
    return AsyncTestHelper()
