"""
契约测试基类

提供端口实现的通用契约测试。
"""

from __future__ import annotations

import pytest
from typing import Type, get_type_hints
from abc import ABC

from architecture import KernelContext


class ContractTest(ABC):
    """
    契约测试基类

    定义端口实现必须通过的测试用例。
    子类实现具体的测试逻辑。
    """

    @pytest.fixture
    def adapter(self):
        """由子类提供具体适配器实例"""
        raise NotImplementedError

    @pytest.fixture
    def context(self):
        """提供测试上下文"""
        return KernelContext(metadata={"test": True})

    def test_interface_methods_exist(self, adapter):
        """测试接口方法存在"""
        import inspect

        for method_name in self.get_required_methods():
            assert hasattr(adapter, method_name), f"Missing method: {method_name}"

            method = getattr(adapter, method_name)
            assert callable(method), f"{method_name} is not callable"

    def get_required_methods(self) -> list[str]:
        """返回接口要求的必需方法列表"""
        raise NotImplementedError


class MemoryPortContract(ContractTest):
    """记忆端口契约测试"""

    @pytest.fixture
    def adapter(self):
        raise NotImplementedError

    @pytest.fixture
    def sample_memory(self):
        from architecture.ports.memory import Memory, MemoryType, MemoryPriority
        return Memory(
            id="contract-mem-1",
            content="测试记忆内容",
            type=MemoryType.SEMANTIC,
            priority=MemoryPriority.MEDIUM,
            agent_id="contract-agent",
        )

    @pytest.fixture
    def memory_query(self):
        from architecture.ports.memory import MemoryQuery
        return MemoryQuery(text="测试", limit=5)

    def get_required_methods(self) -> list[str]:
        return [
            "store",
            "retrieve",
            "get",
            "update",
            "delete",
            "consolidate",
            "search_similar",
            "get_recent",
            "get_stats",
            "clear_session",
        ]

    @pytest.mark.asyncio
    async def test_store_returns_id(self, adapter, sample_memory):
        """测试 store 返回记忆 ID"""
        memory_id = await adapter.store(sample_memory)
        assert memory_id is not None
        assert isinstance(memory_id, str)
        assert len(memory_id) > 0

    @pytest.mark.asyncio
    async def test_store_batch_returns_ids(self, adapter, sample_memory):
        """测试批量存储"""
        memories = [
            sample_memory,
            sample_memory.__class__(
                id="contract-mem-2",
                content="第二个测试记忆",
                type=MemoryType.SEMANTIC,
                priority=MemoryPriority.MEDIUM,
                agent_id="contract-agent",
            ),
        ]
        ids = await adapter.store_batch(memories)
        assert len(ids) == 2
        assert all(isinstance(i, str) for i in ids)

    @pytest.mark.asyncio
    async def test_retrieve_returns_results(self, adapter, memory_query):
        """测试检索返回结果列表"""
        results = await adapter.retrieve(memory_query)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_get_returns_memory_or_none(self, adapter):
        """测试 get 返回记忆或 None"""
        memory = await adapter.get("non-existent-id")
        assert memory is None or hasattr(memory, "id")

    @pytest.mark.asyncio
    async def test_update_returns_bool(self, adapter, sample_memory):
        """测试 update 返回布尔值"""
        stored_id = await adapter.store(sample_memory)
        sample_memory.id = stored_id
        sample_memory.content = "更新后的内容"

        result = await adapter.update(sample_memory)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_delete_returns_bool(self, adapter, sample_memory):
        """测试 delete 返回布尔值"""
        stored_id = await adapter.store(sample_memory)
        result = await adapter.delete(stored_id)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_consolidate_returns_result(self, adapter):
        """测试整合返回结果"""
        from architecture.ports.memory import ConsolidationContext
        context = ConsolidationContext(agent_id="contract-agent")
        result = await adapter.consolidate(context)
        assert hasattr(result, "success")
        assert hasattr(result, "memories_processed")

    @pytest.mark.asyncio
    async def test_search_similar_returns_list(self, adapter):
        """测试相似搜索"""
        results = await adapter.search_similar("测试内容", limit=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_get_recent_returns_list(self, adapter):
        """测试获取最近记忆"""
        results = await adapter.get_recent("contract-agent", limit=10)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_get_stats_returns_stats(self, adapter):
        """测试获取统计信息"""
        stats = await adapter.get_stats()
        assert hasattr(stats, "total_memories")

    @pytest.mark.asyncio
    async def test_clear_session_returns_int(self, adapter):
        """测试清除会话"""
        count = await adapter.clear_session("test-session")
        assert isinstance(count, int)


class ToolPortContract(ContractTest):
    """工具端口契约测试"""

    @pytest.fixture
    def adapter(self):
        raise NotImplementedError

    @pytest.fixture
    def sample_tool(self):
        from architecture.ports.tools import Tool, ToolCategory
        return Tool(
            name="contract_test_tool",
            description="合同测试工具",
            input_schema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                },
                "required": ["input"],
            },
            category=ToolCategory.GENERAL,
        )

    @pytest.fixture
    def tool_call(self):
        from architecture.ports.tools import ToolCall, ToolContext
        return ToolCall(
            id="contract-call-1",
            name="contract_test_tool",
            arguments={"input": "test"},
        )

    @pytest.fixture
    def tool_context(self):
        from architecture.ports.tools import ToolContext
        return ToolContext(
            session_id="contract-session",
            agent_id="contract-agent",
        )

    def get_required_methods(self) -> list[str]:
        return [
            "execute",
            "batch_execute",
            "list_tools",
            "get_tool",
            "validate",
            "register_tool",
            "unregister_tool",
            "search_tools",
        ]

    @pytest.mark.asyncio
    async def test_execute_returns_result(self, adapter, tool_call, tool_context):
        """测试执行返回结果"""
        result = await adapter.execute(tool_call, tool_context)
        assert hasattr(result, "success")
        assert hasattr(result, "call_id")

    @pytest.mark.asyncio
    async def test_batch_execute_returns_list(self, adapter, tool_call, tool_context):
        """测试批量执行返回列表"""
        results = await adapter.batch_execute([tool_call], tool_context)
        assert isinstance(results, list)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_list_tools_returns_list(self, adapter, tool_context):
        """测试列出工具"""
        tools = adapter.list_tools(tool_context)
        assert isinstance(tools, list)

    @pytest.mark.asyncio
    async def test_get_tool_returns_tool_or_none(self, adapter):
        """测试获取工具"""
        tool = adapter.get_tool("non-existent-tool")
        assert tool is None or hasattr(tool, "name")

    @pytest.mark.asyncio
    async def test_validate_returns_result(self, adapter, tool_call, tool_context):
        """测试验证"""
        result = await adapter.validate(tool_call, tool_context)
        assert hasattr(result, "valid")

    @pytest.mark.asyncio
    async def test_register_tool_returns_bool(self, adapter, sample_tool):
        """测试注册工具"""
        result = await adapter.register_tool(sample_tool)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_unregister_tool_returns_bool(self, adapter):
        """测试注销工具"""
        result = await adapter.unregister_tool("non-existent-tool")
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_search_tools_returns_list(self, adapter):
        """测试搜索工具"""
        results = await adapter.search_tools("test")
        assert isinstance(results, list)


class ModelPortContract(ContractTest):
    """模型端口契约测试"""

    @pytest.fixture
    def adapter(self):
        raise NotImplementedError

    @pytest.fixture
    def messages(self):
        from architecture.ports.model import Message, MessageRole
        return [
            Message(role=MessageRole.SYSTEM, content="你是测试助手"),
            Message(role=MessageRole.USER, content="你好"),
        ]

    @pytest.fixture
    def model_config(self):
        from architecture.ports.model import ModelConfig, ModelProvider
        return ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model="claude-test",
            max_tokens=100,
        )

    def get_required_methods(self) -> list[str]:
        return [
            "chat",
            "embed",
            "batch_chat",
            "supports_tools",
            "supports_streaming",
            "supports_vision",
            "supports_thinking",
            "get_context_window",
            "get_max_output_tokens",
        ]

    @pytest.mark.asyncio
    async def test_chat_returns_response(self, adapter, messages, model_config):
        """测试聊天返回响应"""
        response = await adapter.chat(messages, model_config)
        assert hasattr(response, "content")
        assert hasattr(response, "stop_reason")

    @pytest.mark.asyncio
    async def test_embed_returns_response(self, adapter, model_config):
        """测试嵌入返回响应"""
        response = await adapter.embed(["测试文本"], model_config)
        assert hasattr(response, "embeddings")

    @pytest.mark.asyncio
    async def test_batch_chat_returns_list(self, adapter, messages, model_config):
        """测试批量聊天"""
        from architecture.ports.model import BatchChatRequest
        requests = [
            BatchChatRequest(id="1", messages=messages),
            BatchChatRequest(id="2", messages=messages),
        ]
        results = await adapter.batch_chat(requests, model_config)
        assert isinstance(results, list)
        assert len(results) == 2

    def test_supports_tools_returns_bool(self, adapter):
        """测试工具支持"""
        result = adapter.supports_tools()
        assert isinstance(result, bool)

    def test_supports_streaming_returns_bool(self, adapter):
        """测试流式支持"""
        result = adapter.supports_streaming()
        assert isinstance(result, bool)

    def test_supports_vision_returns_bool(self, adapter):
        """测试视觉支持"""
        result = adapter.supports_vision()
        assert isinstance(result, bool)

    def test_supports_thinking_returns_bool(self, adapter):
        """测试思考支持"""
        result = adapter.supports_thinking()
        assert isinstance(result, bool)

    def test_get_context_window_returns_int(self, adapter):
        """测试上下文窗口"""
        result = adapter.get_context_window()
        assert isinstance(result, int)
        assert result > 0

    def test_get_max_output_tokens_returns_int(self, adapter):
        """测试最大输出"""
        result = adapter.get_max_output_tokens()
        assert isinstance(result, int)
        assert result > 0


class CollaborationPortContract(ContractTest):
    """协作端口契约测试"""

    @pytest.fixture
    def adapter(self):
        raise NotImplementedError

    @pytest.fixture
    def agent_message(self):
        from architecture.ports.collaboration import AgentMessage, MessageType
        return AgentMessage(
            id="contract-msg-1",
            sender_id="agent-1",
            receiver_id="agent-2",
            message_type=MessageType.TASK,
            content="测试消息",
        )

    def get_required_methods(self) -> list[str]:
        return [
            "send_message",
            "receive_message",
            "delegate_task",
            "register_agent",
            "unregister_agent",
            "get_agent_health",
            "broadcast_status",
        ]

    @pytest.mark.asyncio
    async def test_send_message_returns_bool(self, adapter, agent_message):
        """测试发送消息"""
        result = await adapter.send_message(agent_message)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_receive_message_returns_or_none(self, adapter):
        """测试接收消息"""
        result = await adapter.receive_message("agent-1", timeout=0.1)
        assert result is None or hasattr(result, "id")

    @pytest.mark.asyncio
    async def test_register_agent_returns_bool(self, adapter):
        """测试注册 Agent"""
        from architecture.ports.collaboration import AgentRole
        result = await adapter.register_agent("test-agent", AgentRole.WORKER, None)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_unregister_agent_returns_bool(self, adapter):
        """测试注销 Agent"""
        result = await adapter.unregister_agent("test-agent")
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_get_agent_health_returns_or_none(self, adapter):
        """测试获取健康状态"""
        result = await adapter.get_agent_health("test-agent")
        assert result is None or hasattr(result, "agent_id")

    @pytest.mark.asyncio
    async def test_broadcast_status_returns_none(self, adapter):
        """测试广播状态"""
        result = await adapter.broadcast_status("test-agent", "healthy")
        assert result is None
