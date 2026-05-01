"""
工具系统端口 - 六边形架构

定义工具系统的抽象接口，支持多种工具后端。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Awaitable, Callable

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """工具分类"""
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    CODE = "code"
    DATA = "data"
    SYSTEM = "system"
    BROWSER = "browser"
    IM = "im"
    SKILL = "skill"
    MCP = "mcp"
    SCHEDULED = "scheduled"
    AGENT = "agent"
    MEMORY = "memory"
    GENERAL = "general"


class ToolPermission(Enum):
    """工具权限级别"""
    SAFE = "safe"           # 安全工具，无需确认
    RISKY = "risky"         # 风险工具，需确认
    DANGEROUS = "dangerous" # 危险工具，需二次确认
    RESTRICTED = "restricted" # 受限工具，需管理员权限


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    input_schema: dict[str, Any]
    category: ToolCategory = ToolCategory.GENERAL
    permission: ToolPermission = ToolPermission.SAFE
    is_concurrent_safe: bool = True
    is_read_only: bool = False
    is_destructive: bool = False
    examples: list[dict[str, Any]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_llm_schema(self) -> dict[str, Any]:
        """转换为 LLM 函数调用格式"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass
class ToolCall:
    """工具调用请求"""
    id: str
    name: str
    arguments: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: str = ""
    agent_id: str = ""
    correlation_id: str | None = None


@dataclass
class ToolResult:
    """工具调用结果"""
    call_id: str
    tool_name: str
    success: bool
    output: str = ""
    error: str | None = None
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_error(self) -> bool:
        return not self.success

    @property
    def formatted_output(self) -> str:
        if self.is_error:
            return f"[Error] {self.error}"
        return self.output


@dataclass
class ToolValidationResult:
    """工具验证结果"""
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ToolContext:
    """工具执行上下文"""
    session_id: str = ""
    agent_id: str = ""
    user_id: str = ""
    cwd: str = ""
    env: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class ToolPort(ABC):
    """
    工具系统端口

    定义工具系统的核心操作接口。
    """

    @abstractmethod
    async def execute(
        self,
        tool_call: ToolCall,
        context: ToolContext,
    ) -> ToolResult:
        """
        执行工具调用

        Args:
            tool_call: 工具调用请求
            context: 执行上下文

        Returns:
            工具执行结果
        """
        pass

    @abstractmethod
    async def batch_execute(
        self,
        tool_calls: list[ToolCall],
        context: ToolContext,
        parallel: bool = True,
    ) -> list[ToolResult]:
        """
        批量执行工具调用

        Args:
            tool_calls: 工具调用请求列表
            context: 执行上下文
            parallel: 是否并行执行

        Returns:
            工具执行结果列表
        """
        pass

    @abstractmethod
    def list_tools(self, context: ToolContext) -> list[Tool]:
        """
        列出可用工具

        Args:
            context: 列表上下文

        Returns:
            可用工具列表
        """
        pass

    @abstractmethod
    def get_tool(self, name: str) -> Tool | None:
        """
        获取工具定义

        Args:
            name: 工具名称

        Returns:
            工具定义，不存在则返回 None
        """
        pass

    @abstractmethod
    async def validate(
        self,
        tool_call: ToolCall,
        context: ToolContext,
    ) -> ToolValidationResult:
        """
        验证工具调用

        Args:
            tool_call: 工具调用请求
            context: 验证上下文

        Returns:
            验证结果
        """
        pass

    @abstractmethod
    async def register_tool(self, tool: Tool) -> bool:
        """
        注册工具

        Args:
            tool: 工具定义

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def unregister_tool(self, name: str) -> bool:
        """
        注销工具

        Args:
            name: 工具名称

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def search_tools(
        self,
        query: str,
        limit: int = 10,
    ) -> list[Tool]:
        """
        搜索工具

        Args:
            query: 搜索关键词
            limit: 返回数量

        Returns:
            匹配的工具列表
        """
        pass


class ToolHandler(ABC):
    """
    工具处理器抽象

    定义单个工具的执行逻辑。
    """

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def tool_schema(self) -> dict[str, Any]:
        """工具 schema"""
        pass

    @abstractmethod
    async def handle(
        self,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """
        处理工具调用

        Args:
            arguments: 工具参数
            context: 执行上下文

        Returns:
            执行结果
        """
        pass

    async def validate(self, arguments: dict[str, Any]) -> ToolValidationResult:
        """
        验证参数

        默认实现检查必需参数。
        子类可重写。
        """
        errors = []
        schema = self.tool_schema.get("input_schema", {})
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        for req in required:
            if req not in arguments:
                errors.append(f"Missing required parameter: {req}")

        return ToolValidationResult(valid=len(errors) == 0, errors=errors)


ToolHandlerFactory = Callable[[], Awaitable[ToolHandler]]


class ToolAdapter(ToolPort):
    """
    工具系统适配器基类

    提供通用适配逻辑，子类实现具体后端。
    """

    def __init__(self, config: ToolAdapterConfig | None = None):
        self.config = config or ToolAdapterConfig()
        self._initialized = False
        self._handlers: dict[str, ToolHandler] = {}

    async def initialize(self) -> None:
        """初始化适配器"""
        if self._initialized:
            return
        await self._do_initialize()
        self._initialized = True

    @abstractmethod
    async def _do_initialize(self) -> None:
        """子类实现具体初始化逻辑"""
        pass

    async def execute(
        self,
        tool_call: ToolCall,
        context: ToolContext,
    ) -> ToolResult:
        await self.initialize()
        return await self._do_execute(tool_call, context)

    async def batch_execute(
        self,
        tool_calls: list[ToolCall],
        context: ToolContext,
        parallel: bool = True,
    ) -> list[ToolResult]:
        await self.initialize()
        return await self._do_batch_execute(tool_calls, context, parallel)

    def list_tools(self, context: ToolContext) -> list[Tool]:
        self.initialize()
        return self._do_list_tools(context)

    def get_tool(self, name: str) -> Tool | None:
        self.initialize()
        return self._do_get_tool(name)

    async def validate(
        self,
        tool_call: ToolCall,
        context: ToolContext,
    ) -> ToolValidationResult:
        await self.initialize()
        return await self._do_validate(tool_call, context)

    async def register_tool(self, tool: Tool) -> bool:
        await self.initialize()
        return await self._do_register_tool(tool)

    async def unregister_tool(self, name: str) -> bool:
        await self.initialize()
        return await self._do_unregister_tool(name)

    async def search_tools(
        self,
        query: str,
        limit: int = 10,
    ) -> list[Tool]:
        await self.initialize()
        return await self._do_search_tools(query, limit)

    def register_handler(self, handler: ToolHandler) -> None:
        """注册工具处理器"""
        self._handlers[handler.tool_name] = handler

    async def _do_execute(
        self,
        tool_call: ToolCall,
        context: ToolContext,
    ) -> ToolResult:
        handler = self._handlers.get(tool_call.name)
        if not handler:
            return ToolResult(
                call_id=tool_call.id,
                tool_name=tool_call.name,
                success=False,
                error=f"Unknown tool: {tool_call.name}",
            )

        import time
        start = time.time()

        try:
            result = await handler.handle(tool_call.arguments, context)
            result.execution_time_ms = (time.time() - start) * 1000
            return result
        except Exception as e:
            return ToolResult(
                call_id=tool_call.id,
                tool_name=tool_call.name,
                success=False,
                error=str(e),
                execution_time_ms=(time.time() - start) * 1000,
            )

    async def _do_batch_execute(
        self,
        tool_calls: list[ToolCall],
        context: ToolContext,
        parallel: bool = True,
    ) -> list[ToolResult]:
        if not parallel:
            return [await self.execute(tc, context) for tc in tool_calls]

        import asyncio
        results = await asyncio.gather(*[
            self.execute(tc, context) for tc in tool_calls
        ], return_exceptions=True)

        output = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                output.append(ToolResult(
                    call_id=tool_calls[i].id,
                    tool_name=tool_calls[i].name,
                    success=False,
                    error=str(result),
                ))
            else:
                output.append(result)
        return output

    def _do_list_tools(self, context: ToolContext) -> list[Tool]:
        return [
            Tool(
                name=h.tool_name,
                description=h.tool_schema.get("description", ""),
                input_schema=h.tool_schema.get("input_schema", {}),
            )
            for h in self._handlers.values()
        ]

    def _do_get_tool(self, name: str) -> Tool | None:
        handler = self._handlers.get(name)
        if not handler:
            return None
        return Tool(
            name=handler.tool_name,
            description=handler.tool_schema.get("description", ""),
            input_schema=handler.tool_schema.get("input_schema", {}),
        )

    async def _do_validate(
        self,
        tool_call: ToolCall,
        context: ToolContext,
    ) -> ToolValidationResult:
        handler = self._handlers.get(tool_call.name)
        if not handler:
            return ToolValidationResult(
                valid=False,
                errors=[f"Unknown tool: {tool_call.name}"],
            )
        return await handler.validate(tool_call.arguments)

    async def _do_register_tool(self, tool: Tool) -> bool:
        return False

    async def _do_unregister_tool(self, name: str) -> bool:
        if name in self._handlers:
            del self._handlers[name]
            return True
        return False

    async def _do_search_tools(
        self,
        query: str,
        limit: int = 10,
    ) -> list[Tool]:
        query_lower = query.lower()
        results = []
        for handler in self._handlers.values():
            if (query_lower in handler.tool_name.lower() or
                query_lower in handler.tool_schema.get("description", "").lower()):
                results.append(Tool(
                    name=handler.tool_name,
                    description=handler.tool_schema.get("description", ""),
                    input_schema=handler.tool_schema.get("input_schema", {}),
                ))
                if len(results) >= limit:
                    break
        return results

    @abstractmethod
    async def _do_initialize(self) -> None:
        pass


@dataclass
class ToolAdapterConfig:
    """工具适配器配置"""
    enabled_tools: list[str] = field(default_factory=list)
    disabled_tools: list[str] = field(default_factory=list)
    max_concurrent: int = 5
    timeout_seconds: float = 60.0
    enable_sandbox: bool = True
    sandbox_timeout_seconds: float = 30.0


class ToolRegistry:
    """工具适配器注册表"""

    _adapters: dict[str, type[ToolAdapter]] = {}

    @classmethod
    def register(cls, name: str, adapter_class: type[ToolAdapter]) -> None:
        cls._adapters[name] = adapter_class

    @classmethod
    def create(cls, name: str, config: ToolAdapterConfig | None = None) -> ToolAdapter:
        adapter_class = cls._adapters.get(name)
        if not adapter_class:
            raise ValueError(f"Unknown tool adapter: {name}")
        return adapter_class(config)

    @classmethod
    def list_adapters(cls) -> list[str]:
        return list(cls._adapters.keys())
