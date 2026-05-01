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
    pass

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
