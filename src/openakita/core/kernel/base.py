from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path

class BaseKernel(ABC):
    """Agent 核心循环接口"""
    @abstractmethod
    async def run_task(self, task: str, **kwargs) -> Any:
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        pass

class BaseShadowWorkspace(ABC):
    """影子工作区接口，支持 Git 级回溯"""
    @abstractmethod
    def resolve_path(self, path: str) -> Path:
        pass

    @abstractmethod
    async def commit(self):
        pass

    @abstractmethod
    async def rollback(self):
        pass

    @abstractmethod
    def get_history(self) -> List[Dict[str, Any]]:
        """获取操作历史树"""
        pass

class BaseMemoryProvider(ABC):
    """记忆提供者接口"""
    @abstractmethod
    async def store(self, content: Any, metadata: Dict[str, Any]):
        pass

    @abstractmethod
    async def query(self, query: str, limit: int = 5) -> List[Any]:
        pass

    @abstractmethod
    async def consolidate(self):
        """记忆整理/结晶"""
        pass
