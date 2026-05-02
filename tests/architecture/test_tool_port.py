"""
ToolPort TDD 测试

遵循 TDD 流程：Red-Green-Refactor
测试工具系统端口的核心功能。
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC_PATH = str(Path(__file__).resolve().parent.parent.parent / "src")
sys.path.insert(0, SRC_PATH)

import pytest

from openakita.architecture.ports.tools import (
    ToolPort,
    ToolAdapter,
    ToolRegistry,
    ToolHandler,
    Tool,
    ToolCategory,
    ToolPermission,
    ToolCall,
    ToolResult,
    ToolValidationResult,
    ToolContext,
    ToolAdapterConfig,
)


class EchoToolHandler(ToolHandler):
    """简单的 Echo 工具处理器"""

    @property
    def tool_name(self) -> str:
        return "echo"

    @property
    def tool_schema(self) -> dict:
        return {
            "description": "Echoes the input back",
            "input_schema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                },
                "required": ["message"],
            },
        }

    async def handle(self, arguments: dict, context: ToolContext) -> ToolResult:
        message = arguments.get("message", "")
        return ToolResult(
            call_id="test-call",
            tool_name=self.tool_name,
            success=True,
            output=f"Echo: {message}",
        )


class MockToolAdapter(ToolAdapter):
    """用于测试的 Mock 工具适配器"""

    async def _do_initialize(self) -> None:
        pass


class TestTool:
    """Tool 测试"""

    def test_tool_has_required_fields(self):
        """Tool 有必需字段"""
        tool = Tool(
            name="test_tool",
            description="测试工具",
            input_schema={"type": "object"},
        )
        assert tool.name == "test_tool"
        assert tool.description == "测试工具"

    def test_tool_has_default_values(self):
        """Tool 有默认值"""
        tool = Tool(
            name="test",
            description="测试",
            input_schema={},
        )
        assert tool.category == ToolCategory.GENERAL
        assert tool.permission == ToolPermission.SAFE
        assert tool.is_concurrent_safe is True

    def test_tool_to_llm_schema(self):
        """Tool 可以转换为 LLM schema"""
        tool = Tool(
            name="test",
            description="测试",
            input_schema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                },
            },
        )
        schema = tool.to_llm_schema()
        assert schema["name"] == "test"
        assert "input_schema" in schema


class TestToolCategory:
    """ToolCategory 测试"""

    def test_categories_exist(self):
        """类别存在"""
        assert ToolCategory.FILESYSTEM.value == "filesystem"
        assert ToolCategory.NETWORK.value == "network"
        assert ToolCategory.CODE.value == "code"
        assert ToolCategory.SYSTEM.value == "system"


class TestToolPermission:
    """ToolPermission 测试"""

    def test_permissions_exist(self):
        """权限级别存在"""
        assert ToolPermission.SAFE.value == "safe"
        assert ToolPermission.RISKY.value == "risky"
        assert ToolPermission.DANGEROUS.value == "dangerous"


class TestToolCall:
    """ToolCall 测试"""

    def test_tool_call_has_required_fields(self):
        """ToolCall 有必需字段"""
        call = ToolCall(
            id="call-1",
            name="test_tool",
            arguments={"input": "test"},
        )
        assert call.id == "call-1"
        assert call.name == "test_tool"
        assert call.arguments["input"] == "test"


class TestToolResult:
    """ToolResult 测试"""

    def test_result_success(self):
        """成功的结果"""
        result = ToolResult(
            call_id="call-1",
            tool_name="test",
            success=True,
            output="Result",
        )
        assert result.success is True
        assert result.is_error is False
        assert result.output == "Result"

    def test_result_failure(self):
        """失败的结果"""
        result = ToolResult(
            call_id="call-1",
            tool_name="test",
            success=False,
            error="Error occurred",
        )
        assert result.success is False
        assert result.is_error is True
        assert result.error == "Error occurred"

    def test_formatted_output_error(self):
        """格式化输出错误"""
        result = ToolResult(
            call_id="call-1",
            tool_name="test",
            success=False,
            error="Error",
        )
        assert result.formatted_output == "[Error] Error"


class TestToolValidationResult:
    """ToolValidationResult 测试"""

    def test_valid_result(self):
        """有效的验证结果"""
        result = ToolValidationResult(valid=True)
        assert result.valid is True

    def test_invalid_result(self):
        """无效的验证结果"""
        result = ToolValidationResult(
            valid=False,
            errors=["Missing required field"],
        )
        assert result.valid is False
        assert len(result.errors) == 1


class TestToolContext:
    """ToolContext 测试"""

    def test_context_has_defaults(self):
        """上下文有默认值"""
        ctx = ToolContext()
        assert ctx.session_id == ""
        assert ctx.agent_id == ""


class TestToolHandler:
    """ToolHandler 测试"""

    def test_handler_has_name(self):
        """处理器有名称"""
        handler = EchoToolHandler()
        assert handler.tool_name == "echo"

    @pytest.mark.asyncio
    async def test_handler_execute(self):
        """处理器可以执行"""
        handler = EchoToolHandler()
        ctx = ToolContext()
        result = await handler.handle({"message": "Hello"}, ctx)
        assert result.success is True


class TestToolAdapterBasics:
    """ToolAdapter 基础测试"""

    @pytest.mark.asyncio
    async def test_adapter_initialization(self):
        """适配器初始化"""
        adapter = MockToolAdapter()
        await adapter.initialize()
        assert adapter._initialized is True

    def test_adapter_can_register_handler(self):
        """适配器可以注册处理器"""
        adapter = MockToolAdapter()
        handler = EchoToolHandler()
        adapter.register_handler(handler)
        assert handler.tool_name in adapter._handlers


class TestToolAdapterExecute:
    """ToolAdapter 执行测试"""

    @pytest.mark.asyncio
    async def test_execute_calls_handler(self):
        """执行调用处理器"""
        adapter = MockToolAdapter()
        adapter.register_handler(EchoToolHandler())

        call = ToolCall(id="call-1", name="echo", arguments={"message": "Test"})
        ctx = ToolContext()

        result = await adapter.execute(call, ctx)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        """执行未知工具"""
        adapter = MockToolAdapter()

        call = ToolCall(id="call-1", name="unknown", arguments={})
        ctx = ToolContext()

        result = await adapter.execute(call, ctx)
        assert result.success is False


class TestToolAdapterList:
    """ToolAdapter 列表测试"""

    def test_list_tools(self):
        """列出工具"""
        adapter = MockToolAdapter()
        adapter.register_handler(EchoToolHandler())

        ctx = ToolContext()
        tools = adapter.list_tools(ctx)
        assert len(tools) >= 1

    def test_get_tool(self):
        """获取工具"""
        adapter = MockToolAdapter()
        adapter.register_handler(EchoToolHandler())

        tool = adapter.get_tool("echo")
        assert tool is not None


class TestToolRegistry:
    """ToolRegistry 测试"""

    def test_register_adapter(self):
        """注册适配器"""
        ToolRegistry.register("test", MockToolAdapter)
        adapters = ToolRegistry.list_adapters()
        assert "test" in adapters
