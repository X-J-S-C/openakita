"""
记忆处理器 (v2)

路由各种记忆相关工具到 MemoryManager。
"""

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...core.agent import Agent

logger = logging.getLogger(__name__)


class MemoryHandler:
    """记忆处理器"""

    _SEARCH_TOOLS = {"search_memory", "trace_memory", "search_conversation_traces"}

    _NAVIGATION_GUIDE = (
        "\n[SYSTEM] 你正在搜索记忆。若找到相关 SOP 或事实，请通过 update_working_checkpoint "
        "将其关键点更新到工作记忆中，以避免在接下来的轮次中重复搜索。\n"
    )

    def __init__(self, agent: "Agent"):
        self.agent = agent
        self._guide_injected = False

    def reset_guide(self):
        """重置导航引导注入标志（每 session 调用一次）"""
        self._guide_injected = False

    async def handle(self, tool_name: str, params: dict[str, Any]) -> str:
        """处理工具调用"""
        if tool_name == "consolidate_memories":
            return await self._consolidate_memories(params)
        elif tool_name == "add_memory":
            return self._add_memory(params)
        elif tool_name == "search_memory":
            result = self._search_memory(params)
        elif tool_name == "get_memory_stats":
            return self._get_memory_stats(params)
        elif tool_name == "list_recent_tasks":
            result = self._list_recent_tasks(params)
        elif tool_name == "search_conversation_traces":
            result = self._search_conversation_traces(params)
        elif tool_name == "trace_memory":
            result = self._trace_memory(params)
        elif tool_name == "search_relational_memory":
            result = await self._search_relational_memory(params)
        elif tool_name == "get_session_context":
            return self._get_session_context(params)
        elif tool_name == "visualize_memory_graph":
            return self._visualize_memory_graph(params)
        else:
            return f"❌ Unknown memory tool: {tool_name}"

        if tool_name in self._SEARCH_TOOLS and not self._guide_injected:
            self._guide_injected = True
            return self._NAVIGATION_GUIDE + result
        return result

    async def _consolidate_memories(self, params: dict) -> str:
        try:
            stats = await self.agent.memory_manager.consolidate_daily()
            return f"✅ 记忆整理完成。统计: {stats}"
        except Exception as e:
            return f"❌ 记忆整理失败: {e}"

    def _add_memory(self, params: dict) -> str:
        content = params.get("content", "")
        if not content:
            return "❌ content is required"
        from ..memory.types import Memory, MemoryType

        m = Memory(
            content=content,
            type=MemoryType.FACT,
            source="manual",
        )
        mid = self.agent.memory_manager.add_memory(m)
        return f"✅ 已添加记忆 (ID: {mid})"

    def _search_memory(self, params: dict) -> str:
        query = params.get("query", "")
        results = self.agent.memory_manager.retrieval_engine.retrieve(query)
        return results if results else "未找到相关记忆。"

    def _get_memory_stats(self, params: dict) -> str:
        stats = self.agent.memory_manager.get_stats()
        return f"📊 记忆统计: {stats}"

    def _list_recent_tasks(self, params: dict) -> str:
        # 简化版实现
        return "近期任务列表暂不可用。"

    def _search_conversation_traces(self, params: dict) -> str:
        # 简化版实现
        return "会话追踪搜索暂未配置后端。"

    def _trace_memory(self, params: dict) -> str:
        return "记忆溯源暂不可用。"

    async def _search_relational_memory(self, params: dict) -> str:
        return "关系型记忆搜索暂不可用。"

    def _get_session_context(self, params: dict) -> str:
        return "当前会话上下文摘要暂不可用。"

    def _visualize_memory_graph(self, params: dict) -> str:
        """生成记忆图谱的 Mermaid 展现。"""
        if hasattr(self.agent.memory_manager, "markdown_syncer"):
            mermaid = self.agent.memory_manager.markdown_syncer.generate_graph_mermaid()
            return f"✅ 已生成记忆图谱 (Mermaid 格式):\n\n```mermaid\n{mermaid}\n```\n\n提示：你可以将此代码粘贴到 Mermaid 渲染器中查看，或让我在回复中直接渲染。"
        return "❌ 当前记忆系统不支持图谱可视化。"


def create_handler(agent: "Agent"):
    handler = MemoryHandler(agent)
    return handler.handle
