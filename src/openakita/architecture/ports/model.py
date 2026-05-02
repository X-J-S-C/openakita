"""
模型端口 - 六边形架构

定义 LLM 模型调用的抽象接口，支持多种模型提供商。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """模型提供商"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OPENAI_COMPATIBLE = "openai_compatible"
    OLLAMA = "ollama"
    LOCAL = "local"
    DASHSCOPE = "dashscope"
    DEEPSEEK = "deepseek"
    ZHIPU = "zhipu"


class MessageRole(Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """消息"""
    role: MessageRole
    content: str | list[dict[str, Any]]
    name: str | None = None
    tool_call_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    """工具调用"""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolCallResult:
    """工具调用结果"""
    tool_call_id: str
    content: str
    is_error: bool = False


@dataclass
class ModelUsage:
    """模型使用量"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


@dataclass
class ModelResponse:
    """模型响应"""
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = ""
    usage: ModelUsage = field(default_factory=ModelUsage)
    model: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0

    @property
    def text(self) -> str:
        return self.content


@dataclass
class EmbeddingResponse:
    """嵌入响应"""
    embeddings: list[list[float]]
    model: str = ""
    usage: ModelUsage = field(default_factory=ModelUsage)


@dataclass
class ModelConfig:
    """模型配置"""
    provider: ModelProvider = ModelProvider.ANTHROPIC
    model: str = "claude-sonnet-4-20250514"
    api_key: str = ""
    base_url: str | None = None
    max_tokens: int = 4096
    temperature: float = 1.0
    top_p: float = 1.0
    top_k: int = 40
    timeout: float = 60.0
    retry_count: int = 3
    enable_thinking: bool = False
    thinking_budget_tokens: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelPort(ABC):
    """
    模型端口

    定义 LLM 调用的核心接口。
    """

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        config: ModelConfig | None = None,
    ) -> ModelResponse:
        """
        聊天完成

        Args:
            messages: 消息列表
            config: 模型配置

        Returns:
            模型响应
        """
        pass

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        config: ModelConfig | None = None,
    ) -> EmbeddingResponse:
        """
        文本嵌入

        Args:
            texts: 文本列表
            config: 模型配置

        Returns:
            嵌入响应
        """
        pass

    @abstractmethod
    async def batch_chat(
        self,
        requests: list[BatchChatRequest],
        config: ModelConfig | None = None,
    ) -> list[ModelResponse]:
        """
        批量聊天完成

        Args:
            requests: 批量请求
            config: 模型配置

        Returns:
            响应列表
        """
        pass

    @abstractmethod
    def supports_tools(self) -> bool:
        """检查是否支持工具调用"""
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        """检查是否支持流式输出"""
        pass

    @abstractmethod
    def supports_vision(self) -> bool:
        """检查是否支持视觉输入"""
        pass

    @abstractmethod
    def supports_thinking(self) -> bool:
        """检查是否支持思考模式"""
        pass

    @abstractmethod
    def get_context_window(self) -> int:
        """获取上下文窗口大小"""
        pass

    @abstractmethod
    def get_max_output_tokens(self) -> int:
        """获取最大输出 tokens"""
        pass


@dataclass
class BatchChatRequest:
    """批量聊天请求"""
    id: str
    messages: list[Message]
    config: ModelConfig | None = None


@dataclass
class StreamChunk:
    """流式输出块"""
    type: str  # "text", "tool_call", "usage", "done"
    content: str = ""
    tool_call: ToolCall | None = None
    usage: ModelUsage | None = None


class ModelAdapter(ModelPort):
    """
    模型适配器基类

    提供通用适配逻辑，子类实现具体提供商。
    """

    def __init__(self, config: ModelConfig | None = None):
        self.config = config or ModelConfig()
        self._initialized = False

    async def initialize(self) -> None:
        """初始化适配器"""
        if self._initialized:
            return
        await self._do_initialize()
        self._initialized = True

    async def chat(
        self,
        messages: list[Message],
        config: ModelConfig | None = None,
    ) -> ModelResponse:
        await self.initialize()
        return await self._do_chat(messages, config)

    async def embed(
        self,
        texts: list[str],
        config: ModelConfig | None = None,
    ) -> EmbeddingResponse:
        await self.initialize()
        return await self._do_embed(texts, config)

    async def batch_chat(
        self,
        requests: list[BatchChatRequest],
        config: ModelConfig | None = None,
    ) -> list[ModelResponse]:
        await self.initialize()
        return await self._do_batch_chat(requests, config)

    def supports_tools(self) -> bool:
        return True

    def supports_streaming(self) -> bool:
        return True

    def supports_vision(self) -> bool:
        return True

    def supports_thinking(self) -> bool:
        return False

    def get_context_window(self) -> int:
        return 200000

    def get_max_output_tokens(self) -> int:
        return 4096

    @abstractmethod
    async def _do_initialize(self) -> None:
        """子类实现具体初始化逻辑"""
        pass

    @abstractmethod
    async def _do_chat(
        self,
        messages: list[Message],
        config: ModelConfig | None,
    ) -> ModelResponse:
        """子类实现具体聊天逻辑"""
        pass

    @abstractmethod
    async def _do_embed(
        self,
        texts: list[str],
        config: ModelConfig | None,
    ) -> EmbeddingResponse:
        """子类实现具体嵌入逻辑"""
        pass

    async def _do_batch_chat(
        self,
        requests: list[BatchChatRequest],
        config: ModelConfig | None,
    ) -> list[ModelResponse]:
        """默认实现：顺序执行"""
        results = []
        for req in requests:
            result = await self.chat(req.messages, req.config or config)
            results.append(result)
        return results


class ModelRouter:
    """模型路由器

    根据请求特征自动选择合适的模型。
    """

    def __init__(self, default_adapter: ModelPort):
        self.default_adapter = default_adapter
        self._adapters: dict[ModelProvider, ModelPort] = {}
        self._routing_rules: list[RoutingRule] = []

    def register_adapter(self, provider: ModelProvider, adapter: ModelPort) -> None:
        """注册模型适配器"""
        self._adapters[provider] = adapter

    def add_rule(self, rule: RoutingRule) -> None:
        """添加路由规则"""
        self._routing_rules.append(rule)

    async def chat(
        self,
        messages: list[Message],
        config: ModelConfig | None = None,
    ) -> ModelResponse:
        """路由聊天请求"""
        config = config or ModelConfig()
        adapter = self._select_adapter(config)
        return await adapter.chat(messages, config)

    async def embed(
        self,
        texts: list[str],
        config: ModelConfig | None = None,
    ) -> EmbeddingResponse:
        """路由嵌入请求"""
        config = config or ModelConfig()
        adapter = self._adapters.get(config.provider, self.default_adapter)
        return await adapter.embed(texts, config)

    def _select_adapter(self, config: ModelConfig) -> ModelPort:
        """根据配置选择适配器"""
        for rule in self._routing_rules:
            if rule.matches(config):
                adapter = self._adapters.get(rule.provider)
                if adapter:
                    return adapter

        return self._adapters.get(config.provider, self.default_adapter)


@dataclass
class RoutingRule:
    """路由规则"""
    provider: ModelProvider
    model_pattern: str = "*"
    min_context: int = 0
    max_context: int = 999999999
    requires_tools: bool = False
    requires_vision: bool = False
    requires_thinking: bool = False

    def matches(self, config: ModelConfig) -> bool:
        if config.provider != self.provider:
            return False
        if self.model_pattern != "*" and config.model != self.model_pattern:
            return False
        return True


class ModelRegistry:
    """模型适配器注册表"""

    _adapters: dict[ModelProvider, type[ModelAdapter]] = {}

    @classmethod
    def register(cls, provider: ModelProvider, adapter_class: type[ModelAdapter]) -> None:
        cls._adapters[provider] = adapter_class

    @classmethod
    def create(cls, provider: ModelProvider, config: ModelConfig | None = None) -> ModelAdapter:
        adapter_class = cls._adapters.get(provider)
        if not adapter_class:
            raise ValueError(f"Unknown model provider: {provider}")
        return adapter_class(config)

    @classmethod
    def list_providers(cls) -> list[ModelProvider]:
        return list(cls._adapters.keys())
