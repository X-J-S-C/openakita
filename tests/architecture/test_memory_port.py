"""
MemoryPort TDD 测试

遵循 TDD 流程：Red-Green-Refactor
测试记忆系统端口的核心功能。
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC_PATH = str(Path(__file__).resolve().parent.parent.parent / "src")
sys.path.insert(0, SRC_PATH)

import pytest
from datetime import datetime

from openakita.architecture.ports.memory import (
    MemoryPort,
    MemoryAdapter,
    MemoryRegistry,
    Memory,
    MemoryType,
    MemoryPriority,
    MemoryQuery,
    MemoryResult,
    MemoryStats,
    StoreContext,
    RetrieveContext,
    GetContext,
    UpdateContext,
    DeleteContext,
    ConsolidationContext,
    ConsolidationResult,
    MemoryAdapterConfig,
)


class MockMemoryAdapter(MemoryAdapter):
    """用于测试的 Mock 记忆适配器"""

    def __init__(self, config=None):
        super().__init__(config)
        self._memories: dict[str, Memory] = {}

    async def _do_initialize(self) -> None:
        pass

    async def _do_store(self, memory: Memory, context: StoreContext | None) -> str:
        self._memories[memory.id] = memory
        return memory.id

    async def _do_store_batch(self, memories: list[Memory], context: StoreContext | None) -> list[str]:
        ids = []
        for mem in memories:
            self._memories[mem.id] = mem
            ids.append(mem.id)
        return ids

    async def _do_retrieve(self, query: MemoryQuery, context: RetrieveContext | None) -> list[MemoryResult]:
        results = []
        for mem in self._memories.values():
            if query.memory_type and mem.type != query.memory_type:
                continue
            results.append(MemoryResult(memory=mem, relevance_score=0.8))
        return results[:query.limit]

    async def _do_get(self, memory_id: str, context: GetContext | None) -> Memory | None:
        return self._memories.get(memory_id)

    async def _do_update(self, memory: Memory, context: UpdateContext | None) -> bool:
        if memory.id in self._memories:
            self._memories[memory.id] = memory
            return True
        return False

    async def _do_delete(self, memory_id: str, context: DeleteContext | None) -> bool:
        if memory_id in self._memories:
            del self._memories[memory_id]
            return True
        return False

    async def _do_consolidate(self, context: ConsolidationContext) -> ConsolidationResult:
        return ConsolidationResult(
            success=True,
            memories_processed=len(self._memories),
            memories_consolidated=0,
            memories_forgotten=0,
        )


class TestMemory:
    """Memory 测试"""

    def test_memory_has_required_fields(self):
        """Memory 有必需字段"""
        memory = Memory(
            id="mem-1",
            content="测试内容",
        )
        assert memory.id == "mem-1"
        assert memory.content == "测试内容"

    def test_memory_has_default_values(self):
        """Memory 有默认值"""
        memory = Memory(id="mem-1", content="测试")
        assert memory.type == MemoryType.EPISODIC
        assert memory.priority == MemoryPriority.MEDIUM
        assert memory.importance == 0.5

    def test_memory_can_set_type(self):
        """Memory 可以设置类型"""
        memory = Memory(
            id="mem-1",
            content="测试",
            type=MemoryType.SEMANTIC,
        )
        assert memory.type == MemoryType.SEMANTIC

    def test_memory_access_updates_timestamp(self):
        """访问更新访问时间戳"""
        memory = Memory(id="mem-1", content="测试")
        original_access = memory.accessed_at

        memory.access()

        assert memory.accessed_at > original_access

    def test_memory_update_updates_content_and_timestamp(self):
        """更新内容更新时间戳"""
        memory = Memory(id="mem-1", content="原始内容")
        original_update = memory.updated_at

        memory.update("新内容")

        assert memory.content == "新内容"
        assert memory.updated_at > original_update


class TestMemoryQuery:
    """MemoryQuery 测试"""

    def test_query_has_text(self):
        """查询有文本"""
        query = MemoryQuery(text="测试")
        assert query.text == "测试"

    def test_query_has_vector(self):
        """查询可以有向量"""
        query = MemoryQuery(query_vector=[0.1, 0.2, 0.3])
        assert query.has_vector_query is True
        assert len(query.query_vector) == 3

    def test_query_has_text_query(self):
        """查询有文本查询"""
        query = MemoryQuery(text="测试")
        assert query.has_text_query is True

        empty_query = MemoryQuery(text="")
        assert empty_query.has_text_query is False

    def test_query_has_limits(self):
        """查询有限制"""
        query = MemoryQuery(text="测试", limit=20)
        assert query.limit == 20


class TestMemoryType:
    """MemoryType 测试"""

    def test_memory_types_exist(self):
        """记忆类型存在"""
        assert MemoryType.EPISODIC.value == "episodic"
        assert MemoryType.SEMANTIC.value == "semantic"
        assert MemoryType.PROCEDURAL.value == "procedural"
        assert MemoryType.SCRATCHPAD.value == "scratchpad"
        assert MemoryType.CORE.value == "core"


class TestMemoryPriority:
    """MemoryPriority 测试"""

    def test_priority_levels(self):
        """优先级级别"""
        assert MemoryPriority.LOW.value == 1
        assert MemoryPriority.MEDIUM.value == 2
        assert MemoryPriority.HIGH.value == 3
        assert MemoryPriority.CRITICAL.value == 4


class TestMemoryAdapterBasics:
    """MemoryAdapter 基础测试"""

    @pytest.mark.asyncio
    async def test_adapter_initialization(self):
        """适配器初始化"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()
        assert adapter._initialized is True

    @pytest.mark.asyncio
    async def test_adapter_initialization_is_idempotent(self):
        """适配器初始化是幂等的"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()
        await adapter.initialize()
        assert adapter._initialized is True


class TestMemoryAdapterStore:
    """MemoryAdapter 存储测试"""

    @pytest.mark.asyncio
    async def test_store_returns_id(self):
        """存储返回 ID"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()

        memory = Memory(id="mem-1", content="测试")
        memory_id = await adapter.store(memory)

        assert memory_id == "mem-1"

    @pytest.mark.asyncio
    async def test_store_batch_returns_ids(self):
        """批量存储返回 ID"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()

        memories = [
            Memory(id="mem-1", content="测试1"),
            Memory(id="mem-2", content="测试2"),
        ]
        ids = await adapter.store_batch(memories)

        assert len(ids) == 2
        assert ids == ["mem-1", "mem-2"]


class TestMemoryAdapterRetrieve:
    """MemoryAdapter 检索测试"""

    @pytest.mark.asyncio
    async def test_retrieve_returns_results(self):
        """检索返回结果"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()

        await adapter.store(Memory(id="mem-1", content="测试"))
        await adapter.store(Memory(id="mem-2", content="内容"))

        query = MemoryQuery(text="测试", limit=10)
        results = await adapter.retrieve(query)

        assert len(results) == 1
        assert results[0].memory.id == "mem-1"

    @pytest.mark.asyncio
    async def test_retrieve_with_type_filter(self):
        """按类型过滤检索"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()

        await adapter.store(Memory(id="mem-1", content="情景", type=MemoryType.EPISODIC))
        await adapter.store(Memory(id="mem-2", content="语义", type=MemoryType.SEMANTIC))

        query = MemoryQuery(text="", memory_type=MemoryType.SEMANTIC)
        results = await adapter.retrieve(query)

        assert len(results) == 1
        assert results[0].memory.type == MemoryType.SEMANTIC

    @pytest.mark.asyncio
    async def test_retrieve_respects_limit(self):
        """检索遵守限制"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()

        for i in range(20):
            await adapter.store(Memory(id=f"mem-{i}", content=f"内容{i}"))

        query = MemoryQuery(text="内容", limit=5)
        results = await adapter.retrieve(query)

        assert len(results) == 5


class TestMemoryAdapterGet:
    """MemoryAdapter Get 测试"""

    @pytest.mark.asyncio
    async def test_get_existing_memory(self):
        """获取存在的记忆"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()

        await adapter.store(Memory(id="mem-1", content="测试"))
        memory = await adapter.get("mem-1")

        assert memory is not None
        assert memory.content == "测试"

    @pytest.mark.asyncio
    async def test_get_nonexistent_memory(self):
        """获取不存在的记忆"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()

        memory = await adapter.get("nonexistent")
        assert memory is None


class TestMemoryAdapterUpdate:
    """MemoryAdapter 更新测试"""

    @pytest.mark.asyncio
    async def test_update_existing_memory(self):
        """更新存在的记忆"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()

        await adapter.store(Memory(id="mem-1", content="原始"))
        memory = await adapter.get("mem-1")
        memory.content = "更新后"

        result = await adapter.update(memory)
        assert result is True

        updated = await adapter.get("mem-1")
        assert updated.content == "更新后"

    @pytest.mark.asyncio
    async def test_update_nonexistent_memory(self):
        """更新不存在的记忆"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()

        memory = Memory(id="nonexistent", content="测试")
        result = await adapter.update(memory)
        assert result is False


class TestMemoryAdapterDelete:
    """MemoryAdapter 删除测试"""

    @pytest.mark.asyncio
    async def test_delete_existing_memory(self):
        """删除存在的记忆"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()

        await adapter.store(Memory(id="mem-1", content="测试"))
        result = await adapter.delete("mem-1")

        assert result is True
        assert await adapter.get("mem-1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_memory(self):
        """删除不存在的记忆"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()

        result = await adapter.delete("nonexistent")
        assert result is False


class TestMemoryAdapterSearch:
    """MemoryAdapter 搜索测试"""

    @pytest.mark.asyncio
    async def test_search_similar(self):
        """相似搜索"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()

        await adapter.store(Memory(id="mem-1", content="这是一个关于Python的测试"))
        await adapter.store(Memory(id="mem-2", content="完全不相关的内容"))

        results = await adapter.search_similar("Python编程", limit=5)

        assert len(results) >= 1
        assert any(m.id == "mem-1" for m in results)

    @pytest.mark.asyncio
    async def test_get_recent(self):
        """获取最近的记忆"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()

        for i in range(10):
            await adapter.store(Memory(id=f"mem-{i}", content=f"内容{i}"))

        results = await adapter.get_recent("test-agent", limit=5)

        assert len(results) <= 5


class TestMemoryAdapterConsolidate:
    """MemoryAdapter 整合测试"""

    @pytest.mark.asyncio
    async def test_consolidate(self):
        """整合记忆"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()

        await adapter.store(Memory(id="mem-1", content="测试"))
        await adapter.store(Memory(id="mem-2", content="内容"))

        context = ConsolidationContext(agent_id="test-agent")
        result = await adapter.consolidate(context)

        assert isinstance(result, ConsolidationResult)
        assert result.success is True


class TestMemoryAdapterStats:
    """MemoryAdapter 统计测试"""

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """获取统计"""
        adapter = MockMemoryAdapter()
        await adapter.initialize()

        await adapter.store(Memory(id="mem-1", content="测试"))

        stats = await adapter.get_stats()

        assert isinstance(stats, MemoryStats)
        assert stats.total_memories >= 1


class TestMemoryRegistry:
    """MemoryRegistry 测试"""

    def test_register_adapter(self):
        """注册适配器"""
        MemoryRegistry.register("test", MockMemoryAdapter)
        adapters = MemoryRegistry.list_adapters()
        assert "test" in adapters

    def test_create_adapter(self):
        """创建适配器"""
        MemoryRegistry.register("create-test", MockMemoryAdapter)
        adapter = MemoryRegistry.create("create-test")
        assert isinstance(adapter, MockMemoryAdapter)

    def test_create_nonexistent_adapter_raises(self):
        """创建不存在的适配器抛出异常"""
        with pytest.raises(ValueError):
            MemoryRegistry.create("nonexistent")


class TestConsolidationContext:
    """ConsolidationContext 测试"""

    def test_context_has_required_fields(self):
        """上下文有必需字段"""
        context = ConsolidationContext(agent_id="agent-1")
        assert context.agent_id == "agent-1"
        assert context.force is False


class TestConsolidationResult:
    """ConsolidationResult 测试"""

    def test_result_has_fields(self):
        """结果有字段"""
        result = ConsolidationResult(
            success=True,
            memories_processed=10,
            memories_consolidated=5,
            memories_forgotten=2,
        )
        assert result.success is True
        assert result.memories_processed == 10
