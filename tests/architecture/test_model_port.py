"""
ModelPort TDD 测试

遵循 TDD 流程：Red-Green-Refactor
测试模型网关端口的核心功能。
"""

from __future__ import annotations

import pytest

from architecture.ports.model import (
    ModelPort,
    ModelAdapter,
    ModelRegistry,
    ModelRouter,
    RoutingRule,
    Message,
    MessageRole,
    ToolDefinition,
    ToolCall,
    ToolCallResult,
    ModelResponse,
    ModelUsage,
    EmbeddingResponse,
    ModelConfig,
    ModelProvider,
    BatchChatRequest,
    StreamChunk,
)


class MockModelAdapter(ModelAdapter):
    """用于测试的 Mock 模型适配器"""

    def __init__(self, config=None):
        super().__init__(config)
        self._chat_calls = []
        self._embed_calls = []

    async def _do_initialize(self) -> None:
        pass

    async def _do_chat(self, messages: list[Message], config: ModelConfig | None) -> ModelResponse:
        self._chat_calls.append((messages, config))
        return ModelResponse(
            content="Mock response",
            stop_reason="stop",
            model=self.config.model,
            usage=ModelUsage(
                input_tokens=10,
                output_tokens=20,
                total_tokens=30,
            ),
        )

    async def _do_embed(self, texts: list[str], config: ModelConfig | None) -> EmbeddingResponse:
        self._embed_calls.append((texts, config))
        return EmbeddingResponse(
            embeddings=[[0.1, 0.2, 0.3] for _ in texts],
            model=self.config.model,
            usage=ModelUsage(total_tokens=len(texts) * 3),
        )


class TestMessage:
    """Message 测试"""

    def test_message_has_required_fields(self):
        """Message 有必需字段"""
        msg = Message(role=MessageRole.USER, content="Hello")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"

    def test_message_can_have_name(self):
        """Message 可以有名称"""
        msg = Message(role=MessageRole.ASSISTANT, content="Hi", name="assistant")
        assert msg.name == "assistant"

    def test_message_can_have_tool_call_id(self):
        """Message 可以有工具调用 ID"""
        msg = Message(
            role=MessageRole.TOOL,
            content="Tool result",
            tool_call_id="call-123",
        )
        assert msg.tool_call_id == "call-123"


class TestMessageRole:
    """MessageRole 测试"""

    def test_roles_exist(self):
        """角色存在"""
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.TOOL.value == "tool"


class TestToolDefinition:
    """ToolDefinition 测试"""

    def test_tool_definition_has_fields(self):
        """ToolDefinition 有字段"""
        tool = ToolDefinition(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object"},
        )
        assert tool.name == "test_tool"
        assert tool.description == "Test tool"


class TestToolCall:
    """ToolCall 测试"""

    def test_tool_call_has_fields(self):
        """ToolCall 有字段"""
        call = ToolCall(id="call-1", name="tool", arguments={"key": "value"})
        assert call.id == "call-1"
        assert call.name == "tool"
        assert call.arguments["key"] == "value"


class TestToolCallResult:
    """ToolCallResult 测试"""

    def test_tool_call_result_has_fields(self):
        """ToolCallResult 有字段"""
        result = ToolCallResult(tool_call_id="call-1", content="Result")
        assert result.tool_call_id == "call-1"
        assert result.content == "Result"
        assert result.is_error is False


class TestModelResponse:
    """ModelResponse 测试"""

    def test_response_has_content(self):
        """Response 有内容"""
        resp = ModelResponse(content="Hello")
        assert resp.content == "Hello"

    def test_response_has_tool_calls(self):
        """Response 有工具调用"""
        calls = [ToolCall(id="c1", name="tool", arguments={})]
        resp = ModelResponse(content="", tool_calls=calls)
        assert resp.has_tool_calls is True

    def test_response_has_no_tool_calls(self):
        """Response 没有工具调用"""
        resp = ModelResponse(content="Hello")
        assert resp.has_tool_calls is False

    def test_response_text_property(self):
        """Response text 属性"""
        resp = ModelResponse(content="Hello")
        assert resp.text == "Hello"


class TestModelUsage:
    """ModelUsage 测试"""

    def test_usage_has_defaults(self):
        """Usage 有默认值"""
        usage = ModelUsage()
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0


class TestEmbeddingResponse:
    """EmbeddingResponse 测试"""

    def test_embedding_response_has_embeddings(self):
        """EmbeddingResponse 有嵌入"""
        resp = EmbeddingResponse(
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
        )
        assert len(resp.embeddings) == 2


class TestModelConfig:
    """ModelConfig 测试"""

    def test_config_has_defaults(self):
        """Config 有默认值"""
        config = ModelConfig()
        assert config.provider == ModelProvider.ANTHROPIC
        assert config.temperature == 1.0
        assert config.max_tokens == 4096

    def test_config_can_set_provider(self):
        """Config 可以设置提供商"""
        config = ModelConfig(provider=ModelProvider.OPENAI)
        assert config.provider == ModelProvider.OPENAI

    def test_config_can_set_api_key(self):
        """Config 可以设置 API key"""
        config = ModelConfig(api_key="secret")
        assert config.api_key == "secret"


class TestModelProvider:
    """ModelProvider 测试"""

    def test_providers_exist(self):
        """提供商存在"""
        assert ModelProvider.ANTHROPIC.value == "anthropic"
        assert ModelProvider.OPENAI.value == "openai"
        assert ModelProvider.OLLAMA.value == "ollama"


class TestBatchChatRequest:
    """BatchChatRequest 测试"""

    def test_batch_request_has_fields(self):
        """BatchChatRequest 有字段"""
        request = BatchChatRequest(
            id="req-1",
            messages=[Message(role=MessageRole.USER, content="Hi")],
        )
        assert request.id == "req-1"
        assert len(request.messages) == 1


class TestStreamChunk:
    """StreamChunk 测试"""

    def test_stream_chunk_text(self):
        """流式文本块"""
        chunk = StreamChunk(type="text", content="Hello")
        assert chunk.type == "text"
        assert chunk.content == "Hello"

    def test_stream_chunk_done(self):
        """流式完成块"""
        chunk = StreamChunk(type="done")
        assert chunk.type == "done"


class TestModelAdapterBasics:
    """ModelAdapter 基础测试"""

    @pytest.mark.asyncio
    async def test_adapter_initialization(self):
        """适配器初始化"""
        adapter = MockModelAdapter()
        await adapter.initialize()
        assert adapter._initialized is True

    @pytest.mark.asyncio
    async def test_adapter_initialization_is_idempotent(self):
        """适配器初始化是幂等的"""
        adapter = MockModelAdapter()
        await adapter.initialize()
        await adapter.initialize()
        assert adapter._initialized is True


class TestModelAdapterChat:
    """ModelAdapter Chat 测试"""

    @pytest.mark.asyncio
    async def test_chat_returns_response(self):
        """Chat 返回响应"""
        adapter = MockModelAdapter()
        await adapter.initialize()

        messages = [
            Message(role=MessageRole.SYSTEM, content="You are helpful"),
            Message(role=MessageRole.USER, content="Hello"),
        ]

        response = await adapter.chat(messages)

        assert isinstance(response, ModelResponse)
        assert response.content == "Mock response"
        assert response.stop_reason == "stop"

    @pytest.mark.asyncio
    async def test_chat_tracks_calls(self):
        """Chat 跟踪调用"""
        adapter = MockModelAdapter()
        await adapter.initialize()

        messages = [Message(role=MessageRole.USER, content="Hi")]
        await adapter.chat(messages)

        assert len(adapter._chat_calls) == 1


class TestModelAdapterEmbed:
    """ModelAdapter Embed 测试"""

    @pytest.mark.asyncio
    async def test_embed_returns_response(self):
        """Embed 返回响应"""
        adapter = MockModelAdapter()
        await adapter.initialize()

        response = await adapter.embed(["Hello", "World"])

        assert isinstance(response, EmbeddingResponse)
        assert len(response.embeddings) == 2

    @pytest.mark.asyncio
    async def test_embed_tracks_calls(self):
        """Embed 跟踪调用"""
        adapter = MockModelAdapter()
        await adapter.initialize()

        await adapter.embed(["Test"])

        assert len(adapter._embed_calls) == 1


class TestModelAdapterBatch:
    """ModelAdapter 批量测试"""

    @pytest.mark.asyncio
    async def test_batch_chat(self):
        """批量 Chat"""
        adapter = MockModelAdapter()
        await adapter.initialize()

        messages = [Message(role=MessageRole.USER, content="Hi")]
        requests = [
            BatchChatRequest(id="1", messages=messages),
            BatchChatRequest(id="2", messages=messages),
        ]

        responses = await adapter.batch_chat(requests)

        assert len(responses) == 2


class TestModelAdapterCapabilities:
    """ModelAdapter 能力测试"""

    def test_supports_tools(self):
        """支持工具"""
        adapter = MockModelAdapter()
        assert adapter.supports_tools() is True

    def test_supports_streaming(self):
        """支持流式"""
        adapter = MockModelAdapter()
        assert adapter.supports_streaming() is True

    def test_supports_vision(self):
        """支持视觉"""
        adapter = MockModelAdapter()
        assert adapter.supports_vision() is True

    def test_supports_thinking(self):
        """支持思考"""
        adapter = MockModelAdapter()
        assert adapter.supports_thinking() is False

    def test_get_context_window(self):
        """获取上下文窗口"""
        adapter = MockModelAdapter()
        assert adapter.get_context_window() > 0

    def test_get_max_output_tokens(self):
        """获取最大输出"""
        adapter = MockModelAdapter()
        assert adapter.get_max_output_tokens() > 0


class TestModelRouter:
    """ModelRouter 测试"""

    @pytest.mark.asyncio
    async def test_router_has_default_adapter(self):
        """路由器有默认适配器"""
        default = MockModelAdapter()
        router = ModelRouter(default)
        assert router.default_adapter is default

    @pytest.mark.asyncio
    async def test_router_registers_adapter(self):
        """路由器注册适配器"""
        default = MockModelAdapter()
        router = ModelRouter(default)

        router.register_adapter(ModelProvider.OPENAI, MockModelAdapter())

        messages = [Message(role=MessageRole.USER, content="Hi")]
        response = await router.chat(messages)
        assert response.content == "Mock response"

    @pytest.mark.asyncio
    async def test_router_routes_by_config(self):
        """路由器根据配置路由"""
        default = MockModelAdapter(ModelConfig(provider=ModelProvider.ANTHROPIC))
        router = ModelRouter(default)

        openai_adapter = MockModelAdapter(ModelConfig(provider=ModelProvider.OPENAI))
        router.register_adapter(ModelProvider.OPENAI, openai_adapter)

        messages = [Message(role=MessageRole.USER, content="Hi")]

        response = await router.chat(
            messages,
            ModelConfig(provider=ModelProvider.OPENAI),
        )
        assert response.model == "claude-test"


class TestRoutingRule:
    """RoutingRule 测试"""

    def test_rule_matches_exact_provider(self):
        """规则匹配精确提供商"""
        rule = RoutingRule(provider=ModelProvider.OPENAI)
        config = ModelConfig(provider=ModelProvider.OPENAI)
        assert rule.matches(config) is True

    def test_rule_does_not_match_different_provider(self):
        """规则不匹配不同提供商"""
        rule = RoutingRule(provider=ModelProvider.OPENAI)
        config = ModelConfig(provider=ModelProvider.ANTHROPIC)
        assert rule.matches(config) is False

    def test_rule_with_model_pattern(self):
        """带模型模式的规则"""
        rule = RoutingRule(provider=ModelProvider.ANTHROPIC, model_pattern="claude-*")
        config = ModelConfig(provider=ModelProvider.ANTHROPIC, model="claude-3")
        assert rule.matches(config) is True


class TestModelRegistry:
    """ModelRegistry 测试"""

    def test_register_provider(self):
        """注册提供商"""
        ModelRegistry.register(ModelProvider.OLLAMA, MockModelAdapter)
        providers = ModelRegistry.list_providers()
        assert ModelProvider.OLLAMA in providers

    def test_create_adapter(self):
        """创建适配器"""
        ModelRegistry.register(ModelProvider.LOCAL, MockModelAdapter)
        adapter = ModelRegistry.create(ModelProvider.LOCAL)
        assert isinstance(adapter, MockModelAdapter)

    def test_create_nonexistent_raises(self):
        """创建不存在的抛出异常"""
        with pytest.raises(ValueError):
            ModelRegistry.create(ModelProvider.DASHSCOPE)
