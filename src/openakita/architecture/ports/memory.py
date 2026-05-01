"""
记忆系统端口 - 六边形架构

定义记忆系统的抽象接口，支持多种后端实现。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..kernel import KernelContext

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """记忆类型"""
    EPISODIC = "episodic"      # 情景记忆（对话片段）
    SEMANTIC = "semantic"      # 语义记忆（知识）
    PROCEDURAL = "procedural"  # 程序记忆（技能）
    SCRATCHPAD = "scratchpad"  # 草稿记忆（工作区）
    CORE = "core"              # 核心记忆（长期）


class MemoryPriority(Enum):
    """记忆优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Memory:
    """记忆条目"""
    id: str
    content: str
    type: MemoryType = MemoryType.EPISODIC
    priority: MemoryPriority = MemoryPriority.MEDIUM
    importance: float = 0.5  # 0-1 重要性评分
    agent_id: str = ""
    session_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)
    embeddings: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def access(self) -> None:
        """标记为已访问"""
        self.accessed_at = datetime.now()

    def update(self, content: str) -> None:
        """更新记忆内容"""
        self.content = content
        self.updated_at = datetime.now()


@dataclass
class MemoryQuery:
    """记忆查询"""
    text: str = ""
    query_vector: list[float] | None = None
    memory_type: MemoryType | None = None
    tags: list[str] = field(default_factory=list)
    session_id: str | None = None
    agent_id: str | None = None
    limit: int = 10
    min_relevance: float = 0.0
    time_range: tuple[datetime, datetime] | None = None

    @property
    def has_vector_query(self) -> bool:
        return self.query_vector is not None

    @property
    def has_text_query(self) -> bool:
        return bool(self.text.strip())


@dataclass
class MemoryResult:
    """记忆检索结果"""
    memory: Memory
    relevance_score: float
    match_type: str = "semantic"


@dataclass
class ConsolidationContext:
    """记忆整合上下文"""
    agent_id: str
    session_id: str | None = None
    force: bool = False


@dataclass
class ConsolidationResult:
    """记忆整合结果"""
    success: bool
    memories_processed: int = 0
    memories_consolidated: int = 0
    memories_forgotten: int = 0
    errors: list[str] = field(default_factory=list)


class MemoryPort(ABC):
    """
    记忆系统端口

    定义记忆系统的核心操作接口。
    支持多种后端实现（SQLite、ChromaDB、Redis 等）。
    """

    @abstractmethod
    async def store(
        self,
        memory: Memory,
        context: StoreContext | None = None,
    ) -> str:
        """
        存储记忆

        Args:
            memory: 要存储的记忆
            context: 存储上下文

        Returns:
            记忆 ID
        """
        pass

    @abstractmethod
    async def store_batch(
        self,
        memories: list[Memory],
        context: StoreContext | None = None,
    ) -> list[str]:
        """
        批量存储记忆

        Args:
            memories: 要存储的记忆列表
            context: 存储上下文

        Returns:
            记忆 ID 列表
        """
        pass

    @abstractmethod
    async def retrieve(
        self,
        query: MemoryQuery,
        context: RetrieveContext | None = None,
    ) -> list[MemoryResult]:
        """
        检索记忆

        Args:
            query: 查询条件
            context: 检索上下文

        Returns:
            匹配的记忆列表
        """
        pass

    @abstractmethod
    async def get(
        self,
        memory_id: str,
        context: GetContext | None = None,
    ) -> Memory | None:
        """
        获取单个记忆

        Args:
            memory_id: 记忆 ID
            context: 获取上下文

        Returns:
            记忆条目，不存在则返回 None
        """
        pass

    @abstractmethod
    async def update(
        self,
        memory: Memory,
        context: UpdateContext | None = None,
    ) -> bool:
        """
        更新记忆

        Args:
            memory: 更新后的记忆
            context: 更新上下文

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def delete(
        self,
        memory_id: str,
        context: DeleteContext | None = None,
    ) -> bool:
        """
        删除记忆

        Args:
            memory_id: 记忆 ID
            context: 删除上下文

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def consolidate(
        self,
        context: ConsolidationContext,
    ) -> ConsolidationResult:
        """
        记忆整合

        执行记忆压缩、遗忘和强化。

        Args:
            context: 整合上下文

        Returns:
            整合结果
        """
        pass

    @abstractmethod
    async def search_similar(
        self,
        content: str,
        limit: int = 5,
        threshold: float = 0.7,
    ) -> list[Memory]:
        """
        查找相似记忆

        Args:
            content: 内容片段
            limit: 返回数量
            threshold: 相似度阈值

        Returns:
            相似记忆列表
        """
        pass

    @abstractmethod
    async def get_recent(
        self,
        agent_id: str,
        limit: int = 50,
        memory_type: MemoryType | None = None,
    ) -> list[Memory]:
        """
        获取最近的记忆

        Args:
            agent_id: Agent ID
            limit: 返回数量
            memory_type: 记忆类型过滤

        Returns:
            最近的记忆列表
        """
        pass

    @abstractmethod
    async def get_stats(self) -> MemoryStats:
        """
        获取记忆统计

        Returns:
            记忆统计信息
        """
        pass

    @abstractmethod
    async def clear_session(self, session_id: str) -> int:
        """
        清除会话记忆

        Args:
            session_id: 会话 ID

        Returns:
            删除的记忆数量
        """
        pass


@dataclass
class StoreContext:
    """存储上下文"""
    agent_id: str = ""
    session_id: str = ""
    priority: MemoryPriority = MemoryPriority.MEDIUM
    tags: list[str] = field(default_factory=list)
    skip_embedding: bool = False


@dataclass
class RetrieveContext:
    """检索上下文"""
    agent_id: str = ""
    session_id: str = ""
    include_forgotten: bool = False


@dataclass
class GetContext:
    """获取上下文"""
    agent_id: str = ""
    mark_accessed: bool = True


@dataclass
class UpdateContext:
    """更新上下文"""
    agent_id: str = ""
    update_embeddings: bool = True


@dataclass
class DeleteContext:
    """删除上下文"""
    agent_id: str = ""
    hard_delete: bool = False


@dataclass
class MemoryStats:
    """记忆统计"""
    total_memories: int = 0
    by_type: dict[str, int] = field(default_factory=dict)
    by_agent: dict[str, int] = field(default_factory=dict)
    average_importance: float = 0.0
    oldest_memory: datetime | None = None
    newest_memory: datetime | None = None


class MemoryAdapter(MemoryPort):
    """
    记忆系统适配器基类

    提供通用适配逻辑，子类实现具体后端。
    """

    def __init__(self, config: MemoryAdapterConfig | None = None):
        self.config = config or MemoryAdapterConfig()
        self._initialized = False

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

    async def store(
        self,
        memory: Memory,
        context: StoreContext | None = None,
    ) -> str:
        await self.initialize()
        return await self._do_store(memory, context)

    async def store_batch(
        self,
        memories: list[Memory],
        context: StoreContext | None = None,
    ) -> list[str]:
        await self.initialize()
        return await self._do_store_batch(memories, context)

    async def retrieve(
        self,
        query: MemoryQuery,
        context: RetrieveContext | None = None,
    ) -> list[MemoryResult]:
        await self.initialize()
        return await self._do_retrieve(query, context)

    async def get(
        self,
        memory_id: str,
        context: GetContext | None = None,
    ) -> Memory | None:
        await self.initialize()
        return await self._do_get(memory_id, context)

    async def update(
        self,
        memory: Memory,
        context: UpdateContext | None = None,
    ) -> bool:
        await self.initialize()
        return await self._do_update(memory, context)

    async def delete(
        self,
        memory_id: str,
        context: DeleteContext | None = None,
    ) -> bool:
        await self.initialize()
        return await self._do_delete(memory_id, context)

    async def consolidate(
        self,
        context: ConsolidationContext,
    ) -> ConsolidationResult:
        await self.initialize()
        return await self._do_consolidate(context)

    async def search_similar(
        self,
        content: str,
        limit: int = 5,
        threshold: float = 0.7,
    ) -> list[Memory]:
        await self.initialize()
        query = MemoryQuery(text=content, limit=limit, min_relevance=threshold)
        results = await self.retrieve(query)
        return [r.memory for r in results]

    async def get_recent(
        self,
        agent_id: str,
        limit: int = 50,
        memory_type: MemoryType | None = None,
    ) -> list[Memory]:
        query = MemoryQuery(agent_id=agent_id, memory_type=memory_type, limit=limit)
        results = await self.retrieve(query)
        return [r.memory for r in results]

    async def get_stats(self) -> MemoryStats:
        return MemoryStats()

    async def clear_session(self, session_id: str) -> int:
        return 0

    @abstractmethod
    async def _do_store(self, memory: Memory, context: StoreContext | None) -> str:
        pass

    @abstractmethod
    async def _do_store_batch(self, memories: list[Memory], context: StoreContext | None) -> list[str]:
        pass

    @abstractmethod
    async def _do_retrieve(self, query: MemoryQuery, context: RetrieveContext | None) -> list[MemoryResult]:
        pass

    @abstractmethod
    async def _do_get(self, memory_id: str, context: GetContext | None) -> Memory | None:
        pass

    @abstractmethod
    async def _do_update(self, memory: Memory, context: UpdateContext | None) -> bool:
        pass

    @abstractmethod
    async def _do_delete(self, memory_id: str, context: DeleteContext | None) -> bool:
        pass

    @abstractmethod
    async def _do_consolidate(self, context: ConsolidationContext) -> ConsolidationResult:
        pass


@dataclass
class MemoryAdapterConfig:
    """记忆适配器配置"""
    data_dir: str = "./data"
    max_memories: int = 10000
    embedding_model: str = "auto"
    vector_dim: int = 384
    enable_fts5: bool = True
    enable_chroma: bool = False
    chroma_host: str = "localhost"
    chroma_port: int = 8000


class MemoryRegistry:
    """记忆适配器注册表"""

    _adapters: dict[str, type[MemoryAdapter]] = {}

    @classmethod
    def register(cls, name: str, adapter_class: type[MemoryAdapter]) -> None:
        cls._adapters[name] = adapter_class

    @classmethod
    def create(cls, name: str, config: MemoryAdapterConfig | None = None) -> MemoryAdapter:
        adapter_class = cls._adapters.get(name)
        if not adapter_class:
            raise ValueError(f"Unknown memory adapter: {name}")
        return adapter_class(config)

    @classmethod
    def list_adapters(cls) -> list[str]:
        return list(cls._adapters.keys())
