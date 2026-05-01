"""
多 Agent 协作端口 - 六边形架构

定义多 Agent 协作的核心接口和协议。
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..kernel import AgentKernel, KernelContext

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent 角色"""
    ORCHESTRATOR = "orchestrator"  # 编排器
    WORKER = "worker"              # 工作节点
    SPECIALIST = "specialist"      # 专家
    COORDINATOR = "coordinator"   # 协调器
    SUPERVISOR = "supervisor"     # 监督者


class MessageType(Enum):
    """消息类型"""
    TASK = "task"                 # 任务消息
    RESULT = "result"            # 结果消息
    STATUS = "status"            # 状态消息
    HEARTBEAT = "heartbeat"      # 心跳消息
    ERROR = "error"              # 错误消息
    CONTROL = "control"           # 控制消息


@dataclass
class AgentMessage:
    """Agent 间消息"""
    id: str
    sender_id: str
    receiver_id: str
    message_type: MessageType
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str | None = None
    reply_to: str | None = None


@dataclass
class TaskRequest:
    """任务请求"""
    id: str
    description: str
    priority: int = 0
    deadline: datetime | None = None
    requirements: dict[str, Any] = field(default_factory=dict)
    source_agent_id: str = ""
    target_agent_id: str | None = None
    delegation_depth: int = 0
    max_delegation_depth: int = 5
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaskResult:
    """任务结果"""
    request_id: str
    agent_id: str
    success: bool
    content: str = ""
    error: str | None = None
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    execution_time_ms: float = 0.0
    tools_used: list[str] = field(default_factory=list)
    completed_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentHealth:
    """Agent 健康状态"""
    agent_id: str
    status: str = "healthy"
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_latency_ms: float = 0.0
    last_error: str | None = None
    last_heartbeat: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests


@dataclass
class CollaborationContext:
    """协作上下文"""
    session_id: str
    root_agent_id: str
    current_agent_id: str
    shared_memory_key: str = ""
    enable_shared_context: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class CollaborationPort(ABC):
    """
    协作端口

    定义多 Agent 协作的核心接口。
    """

    @abstractmethod
    async def send_message(
        self,
        message: AgentMessage,
    ) -> bool:
        """
        发送消息

        Args:
            message: 消息

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def receive_message(
        self,
        agent_id: str,
        timeout: float = 30.0,
    ) -> AgentMessage | None:
        """
        接收消息

        Args:
            agent_id: Agent ID
            timeout: 超时时间

        Returns:
            消息，无消息则返回 None
        """
        pass

    @abstractmethod
    async def delegate_task(
        self,
        request: TaskRequest,
        context: CollaborationContext,
    ) -> TaskResult:
        """
        委派任务

        Args:
            request: 任务请求
            context: 协作上下文

        Returns:
            任务结果
        """
        pass

    @abstractmethod
    async def register_agent(
        self,
        agent_id: str,
        role: AgentRole,
        kernel: "AgentKernel",
    ) -> bool:
        """
        注册 Agent

        Args:
            agent_id: Agent ID
            role: Agent 角色
            kernel: Agent 内核

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def unregister_agent(
        self,
        agent_id: str,
    ) -> bool:
        """
        注销 Agent

        Args:
            agent_id: Agent ID

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def get_agent_health(
        self,
        agent_id: str,
    ) -> AgentHealth | None:
        """
        获取 Agent 健康状态

        Args:
            agent_id: Agent ID

        Returns:
            健康状态
        """
        pass

    @abstractmethod
    async def broadcast_status(
        self,
        agent_id: str,
        status: str,
    ) -> None:
        """
        广播状态

        Args:
            agent_id: Agent ID
            status: 状态
        """
        pass


class AgentMailbox:
    """Agent 邮箱"""

    def __init__(self, agent_id: str, maxsize: int = 100):
        self.agent_id = agent_id
        self._queue: asyncio.Queue[AgentMessage] = asyncio.Queue(maxsize=maxsize)

    async def send(self, message: AgentMessage) -> None:
        await self._queue.put(message)

    async def receive(self, timeout: float = 30.0) -> AgentMessage | None:
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    def pending(self) -> int:
        return self._queue.qsize()

    async def drain(self) -> list[AgentMessage]:
        messages = []
        while not self._queue.empty():
            try:
                messages.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return messages


class InProcessCollaborationAdapter(CollaborationPort):
    """
    进程内协作适配器

    用于单个进程内的多 Agent 协作。
    """

    def __init__(self):
        self._agents: dict[str, tuple[AgentRole, "AgentKernel"]] = {}
        self._mailboxes: dict[str, AgentMailbox] = {}
        self._health: dict[str, AgentHealth] = {}

    async def send_message(
        self,
        message: AgentMessage,
    ) -> bool:
        mailbox = self._mailboxes.get(message.receiver_id)
        if not mailbox:
            logger.warning(f"[Collaboration] No mailbox for agent {message.receiver_id}")
            return False

        try:
            await mailbox.send(message)
            return True
        except asyncio.QueueFull:
            logger.error(f"[Collaboration] Mailbox full for agent {message.receiver_id}")
            return False

    async def receive_message(
        self,
        agent_id: str,
        timeout: float = 30.0,
    ) -> AgentMessage | None:
        mailbox = self._mailboxes.get(agent_id)
        if not mailbox:
            return None
        return await mailbox.receive(timeout)

    async def delegate_task(
        self,
        request: TaskRequest,
        context: CollaborationContext,
    ) -> TaskResult:
        start_time = datetime.now()

        if request.target_agent_id:
            agent_id = request.target_agent_id
        else:
            agent_id = await self._select_best_agent(request)

        if not agent_id:
            return TaskResult(
                request_id=request.id,
                agent_id="",
                success=False,
                error="No available agent",
            )

        role, kernel = self._agents.get(agent_id, (None, None))
        if not kernel:
            return TaskResult(
                request_id=request.id,
                agent_id=agent_id,
                success=False,
                error="Agent not found",
            )

        try:
            from ..kernel import KernelContext
            kernel_context = KernelContext(metadata={
                "session_id": context.session_id,
                "agent_id": agent_id,
                "root_agent_id": context.root_agent_id,
            })

            result = await kernel.run(
                type(request).__name__,
                kernel_context,
            )

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return TaskResult(
                request_id=request.id,
                agent_id=agent_id,
                success=result.success,
                content=result.content,
                error=result.error,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            logger.error(f"[Collaboration] Task delegation error: {e}")
            return TaskResult(
                request_id=request.id,
                agent_id=agent_id,
                success=False,
                error=str(e),
            )

    async def register_agent(
        self,
        agent_id: str,
        role: AgentRole,
        kernel: "AgentKernel",
    ) -> bool:
        self._agents[agent_id] = (role, kernel)
        self._mailboxes[agent_id] = AgentMailbox(agent_id)
        self._health[agent_id] = AgentHealth(agent_id=agent_id)
        logger.info(f"[Collaboration] Registered agent: {agent_id} (role={role.value})")
        return True

    async def unregister_agent(
        self,
        agent_id: str,
    ) -> bool:
        if agent_id in self._agents:
            del self._agents[agent_id]
            self._mailboxes.pop(agent_id, None)
            self._health.pop(agent_id, None)
            logger.info(f"[Collaboration] Unregistered agent: {agent_id}")
            return True
        return False

    async def get_agent_health(
        self,
        agent_id: str,
    ) -> AgentHealth | None:
        return self._health.get(agent_id)

    async def broadcast_status(
        self,
        agent_id: str,
        status: str,
    ) -> None:
        health = self._health.get(agent_id)
        if health:
            health.status = status
            health.last_heartbeat = datetime.now()

    async def _select_best_agent(self, request: TaskRequest) -> str | None:
        """选择最佳 Agent"""
        available = []

        for agent_id, (role, _) in self._agents.items():
            if role == AgentRole.WORKER:
                health = self._health.get(agent_id)
                if health and health.status == "healthy":
                    available.append((agent_id, health.success_rate))

        if not available:
            return None

        available.sort(key=lambda x: x[1], reverse=True)
        return available[0][0]


class CollaborationRegistry:
    """协作适配器注册表"""

    _adapters: dict[str, type[CollaborationPort]] = {}

    @classmethod
    def register(cls, name: str, adapter_class: type[CollaborationPort]) -> None:
        cls._adapters[name] = adapter_class

    @classmethod
    def create(cls, name: str = "in_process") -> CollaborationPort:
        adapter_class = cls._adapters.get(name)
        if not adapter_class:
            raise ValueError(f"Unknown collaboration adapter: {name}")
        return adapter_class()

    @classmethod
    def list_adapters(cls) -> list[str]:
        return list(cls._adapters.keys())


CollaborationRegistry.register("in_process", InProcessCollaborationAdapter)
