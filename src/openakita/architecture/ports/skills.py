"""
Skill 端口 - 六边形架构

定义技能系统的抽象接口。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..context import KernelContext

logger = logging.getLogger(__name__)


class SkillCategory(Enum):
    """技能分类"""
    PRODUCTIVITY = "productivity"
    CREATIVE = "creative"
    DEVELOPMENT = "development"
    RESEARCH = "research"
    COMMUNICATION = "communication"
    AUTOMATION = "automation"
    DATA = "data"
    CUSTOM = "custom"


@dataclass
class Skill:
    """技能定义"""
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    source: str = ""
    is_builtin: bool = False
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillResult:
    """技能执行结果"""
    skill_id: str
    success: bool
    output: str = ""
    error: str | None = None
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillInstallResult:
    """技能安装结果"""
    success: bool
    skill: Skill | None = None
    error: str | None = None
    installed_files: list[str] = field(default_factory=list)


class SkillPort(ABC):
    """
    Skills 端口

    定义技能系统的核心接口。
    """

    @abstractmethod
    async def list_skills(
        self,
        context: "KernelContext",
    ) -> list[Skill]:
        """
        列出可用技能

        Args:
            context: 列表上下文

        Returns:
            技能列表
        """
        pass

    @abstractmethod
    async def execute_skill(
        self,
        skill_id: str,
        arguments: dict[str, Any],
        context: "KernelContext",
    ) -> SkillResult:
        """
        执行技能

        Args:
            skill_id: 技能 ID
            arguments: 技能参数
            context: 执行上下文

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    async def install_skill(
        self,
        skill_source: str,
        context: "KernelContext",
    ) -> SkillInstallResult:
        """
        安装技能

        Args:
            skill_source: 技能源（URL、文件路径等）
            context: 安装上下文

        Returns:
            安装结果
        """
        pass

    @abstractmethod
    async def uninstall_skill(
        self,
        skill_id: str,
        context: "KernelContext",
    ) -> bool:
        """
        卸载技能

        Args:
            skill_id: 技能 ID
            context: 卸载上下文

        Returns:
            是否成功
        """
        pass
