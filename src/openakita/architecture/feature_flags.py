"""
特性开关系统

提供运行时特性开关控制，支持灰度发布和 A/B 测试。
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class FeatureGroup(Enum):
    """特性分组"""
    KERNEL = "kernel"
    MEMORY = "memory"
    TOOLS = "tools"
    MODEL = "model"
    SKILLS = "skills"
    MULTI_AGENT = "multi_agent"
    SECURITY = "security"
    OBSERVABILITY = "observability"


@dataclass
class FeatureFlag:
    """特性开关定义"""
    name: str
    description: str
    group: FeatureGroup
    default_value: bool = False
    rollout_percentage: float = 0.0  # 0-100
    environment: str = ""  # 空表示所有环境
    min_version: str = ""  # 最低版本要求
    dependencies: list[str] = field(default_factory=list)  # 依赖的其他开关
    metadata: dict[str, Any] = field(default_factory=dict)


class FeatureFlags:
    """
    特性开关管理器

    支持:
    - 环境变量配置
    - 配置文件配置
    - 灰度百分比
    - 版本约束
    - 特性依赖
    """

    # 核心特性开关
    KERNEL_V2 = "openakita.kernel.v2"
    RALPH_LOOP_V2 = "openakita.loop.v2"
    STATE_MACHINE = "openakita.kernel.state_machine"
    CHECKPOINTING = "openakita.kernel.checkpointing"

    # 记忆系统开关
    MEMORY_V2 = "openakita.memory.v2"
    MEMORY_CHROMA = "openakita.memory.chroma"
    MEMORY_CONSOLIDATION = "openakita.memory.consolidation"
    MEMORY_EMBEDDING_ASYNC = "openakita.memory.embedding_async"

    # 工具系统开关
    TOOL_V2 = "openakita.tools.v2"
    TOOL_MCP_NATIVE = "openakita.tools.mcp_native"
    TOOL_CONCURRENT = "openakita.tools.concurrent"
    TOOL_SANDBOX = "openakita.tools.sandbox"

    # 模型开关
    MODEL_ADAPTER_V2 = "openakita.model.adapter.v2"
    MODEL_STREAMING = "openakita.model.streaming"
    MODEL_THINKING = "openakita.model.thinking"
    MODEL_ROUTING = "openakita.model.routing"

    # 多 Agent 开关
    MULTI_AGENT_ENABLED = "openakita.multi_agent.enabled"
    MULTI_AGENT_ORCHESTRATOR = "openakita.multi_agent.orchestrator"
    MULTI_AGENT_SHARED_MEMORY = "openakita.multi_agent.shared_memory"

    # 安全开关
    SECURITY_RISK_DETECTION = "openakita.security.risk_detection"
    SECURITY_INPUT_VALIDATION = "openakita.security.input_validation"
    SECURITY_OUTPUT_FILTERING = "openakita.security.output_filtering"

    # 可观测性开关
    OBSERVABILITY_TRACING = "openakita.observability.tracing"
    OBSERVABILITY_METRICS = "openakita.observability.metrics"
    OBSERVABILITY_LOGGING = "openakita.observability.logging"

    _flags: dict[str, FeatureFlag] = {}
    _overrides: dict[str, bool] = {}
    _user_overrides: dict[str, Callable[[], bool]] = {}
    _initialized: bool = False

    @classmethod
    def initialize(cls, config_path: str | None = None) -> None:
        """初始化特性开关"""
        if cls._initialized:
            return

        cls._register_default_flags()
        cls._load_from_env()
        if config_path:
            cls._load_from_file(config_path)

        cls._initialized = True
        logger.info(f"[FeatureFlags] Initialized with {len(cls._flags)} flags")

    @classmethod
    def _register_default_flags(cls) -> None:
        """注册默认特性开关"""
        default_flags = [
            FeatureFlag(
                name=cls.KERNEL_V2,
                description="使用新版本 Agent 内核",
                group=FeatureGroup.KERNEL,
                default_value=False,
            ),
            FeatureFlag(
                name=cls.RALPH_LOOP_V2,
                description="使用新版本 Ralph 循环",
                group=FeatureGroup.KERNEL,
                default_value=False,
            ),
            FeatureFlag(
                name=cls.MEMORY_V2,
                description="使用新版本记忆系统",
                group=FeatureGroup.MEMORY,
                default_value=True,
            ),
            FeatureFlag(
                name=cls.MEMORY_CHROMA,
                description="使用 ChromaDB 作为向量存储",
                group=FeatureGroup.MEMORY,
                default_value=False,
            ),
            FeatureFlag(
                name=cls.TOOL_V2,
                description="使用新版本工具系统",
                group=FeatureGroup.TOOLS,
                default_value=False,
            ),
            FeatureFlag(
                name=cls.MODEL_ADAPTER_V2,
                description="使用新版本模型适配器",
                group=FeatureGroup.MODEL,
                default_value=False,
            ),
            FeatureFlag(
                name=cls.MODEL_STREAMING,
                description="启用流式输出",
                group=FeatureGroup.MODEL,
                default_value=True,
            ),
            FeatureFlag(
                name=cls.MULTI_AGENT_ENABLED,
                description="启用多 Agent 模式",
                group=FeatureGroup.MULTI_AGENT,
                default_value=False,
            ),
            FeatureFlag(
                name=cls.SECURITY_RISK_DETECTION,
                description="启用风险检测",
                group=FeatureGroup.SECURITY,
                default_value=True,
            ),
            FeatureFlag(
                name=cls.OBSERVABILITY_TRACING,
                description="启用追踪",
                group=FeatureGroup.OBSERVABILITY,
                default_value=True,
            ),
        ]

        for flag in default_flags:
            cls._flags[flag.name] = flag

    @classmethod
    def _load_from_env(cls) -> None:
        """从环境变量加载"""
        for name, flag in cls._flags.items():
            env_key = f"AKITA_FLAG_{name.upper().replace('.', '_')}"
            value = os.environ.get(env_key)
            if value is not None:
                cls._overrides[name] = value.lower() in ("true", "1", "yes", "on")

    @classmethod
    def _load_from_file(cls, config_path: str) -> None:
        """从配置文件加载"""
        import pathlib
        path = pathlib.Path(config_path)
        if not path.exists():
            return

        try:
            with open(path) as f:
                config = json.load(f)

            flags_config = config.get("feature_flags", {})
            for name, value in flags_config.items():
                if name in cls._flags:
                    if isinstance(value, dict):
                        cls._flags[name].rollout_percentage = value.get("rollout", 0)
                        cls._overrides[name] = value.get("enabled", cls._flags[name].default_value)
                    else:
                        cls._overrides[name] = bool(value)
        except Exception as e:
            logger.warning(f"[FeatureFlags] Failed to load config from {config_path}: {e}")

    @classmethod
    def register_flag(cls, flag: FeatureFlag) -> None:
        """注册新的特性开关"""
        cls._flags[flag.name] = flag

    @classmethod
    def is_enabled(
        cls,
        flag_name: str,
        default: bool = False,
        user_id: str = "",
        session_id: str = "",
    ) -> bool:
        """
        检查特性开关是否启用

        Args:
            flag_name: 开关名称
            default: 默认值
            user_id: 用户 ID（用于灰度）
            session_id: 会话 ID

        Returns:
            是否启用
        """
        if not cls._initialized:
            cls.initialize()

        # 用户覆盖优先
        if flag_name in cls._user_overrides:
            return cls._user_overrides[flag_name]()

        # 环境/配置文件覆盖
        if flag_name in cls._overrides:
            return cls._overrides[flag_name]

        flag = cls._flags.get(flag_name)
        if not flag:
            return default

        # 检查依赖
        for dep in flag.dependencies:
            if not cls.is_enabled(dep, default=False, user_id=user_id, session_id=session_id):
                return False

        # 检查版本约束
        if flag.min_version:
            from .. import __version__
            if cls._compare_version(__version__, flag.min_version) < 0:
                return False

        # 灰度百分比
        if flag.rollout_percentage > 0 and flag.rollout_percentage < 100:
            bucket = cls._get_bucket(user_id or session_id or "default", flag_name)
            return bucket < flag.rollout_percentage

        return flag.default_value

    @classmethod
    def enable(
        cls,
        flag_name: str,
        temporary: bool = False,
    ) -> None:
        """
        临时启用特性开关

        Args:
            flag_name: 开关名称
            temporary: 是否临时（仅当前进程）
        """
        if not temporary:
            cls._flags[flag_name].default_value = True
        cls._overrides[flag_name] = True

    @classmethod
    def disable(
        cls,
        flag_name: str,
        temporary: bool = False,
    ) -> None:
        """
        临时禁用特性开关

        Args:
            flag_name: 开关名称
            temporary: 是否临时（仅当前进程）
        """
        if not temporary:
            cls._flags[flag_name].default_value = False
        cls._overrides[flag_name] = False

    @classmethod
    def set_user_override(
        cls,
        flag_name: str,
        provider: Callable[[], bool],
    ) -> None:
        """设置用户级别覆盖"""
        cls._user_overrides[flag_name] = provider

    @classmethod
    def clear_override(cls, flag_name: str) -> None:
        """清除覆盖"""
        cls._overrides.pop(flag_name, None)
        cls._user_overrides.pop(flag_name, None)

    @classmethod
    def get_flag_info(cls, flag_name: str) -> dict[str, Any]:
        """获取开关信息"""
        flag = cls._flags.get(flag_name)
        if not flag:
            return {}

        return {
            "name": flag.name,
            "description": flag.description,
            "group": flag.group.value,
            "enabled": cls.is_enabled(flag_name),
            "default_value": flag.default_value,
            "rollout_percentage": flag.rollout_percentage,
        }

    @classmethod
    def list_flags(cls, group: FeatureGroup | None = None) -> list[dict[str, Any]]:
        """列出所有开关"""
        flags = []
        for name, flag in cls._flags.items():
            if group and flag.group != group:
                continue
            flags.append(cls.get_flag_info(name))
        return flags

    @classmethod
    def _get_bucket(cls, identifier: str, flag_name: str) -> float:
        """根据标识符计算灰度桶"""
        import hashlib
        key = f"{flag_name}:{identifier}"
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return (hash_value % 10000) / 100.0

    @classmethod
    def _compare_version(cls, version: str, min_version: str) -> int:
        """比较版本号"""
        v1_parts = [int(x) for x in version.split(".")]
        v2_parts = [int(x) for x in min_version.split(".")]

        for i in range(max(len(v1_parts), len(v2_parts))):
            v1 = v1_parts[i] if i < len(v1_parts) else 0
            v2 = v2_parts[i] if i < len(v2_parts) else 0
            if v1 > v2:
                return 1
            if v1 < v2:
                return -1
        return 0


@dataclass
class FeatureGate:
    """
    特性门控

    装饰器形式使用特性开关。
    """

    flag_name: str
    default: bool = False
    fallback: Callable[[], Any] | None = None

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """装饰函数"""
        def wrapper(*args, **kwargs) -> T:
            if FeatureFlags.is_enabled(self.flag_name, self.default):
                return func(*args, **kwargs)
            elif self.fallback:
                return self.fallback()
            raise FeatureDisabledError(self.flag_name)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    async def __call_async__(self, func: Callable[..., T], *args, **kwargs) -> T:
        """异步装饰函数"""
        if FeatureFlags.is_enabled(self.flag_name, self.default):
            return await func(*args, **kwargs)
        elif self.fallback:
            return self.fallback()
        raise FeatureDisabledError(self.flag_name)


class FeatureDisabledError(Exception):
    """特性未启用异常"""

    def __init__(self, flag_name: str):
        self.flag_name = flag_name
        super().__init__(f"Feature '{flag_name}' is disabled")


class RolloutManager:
    """
    灰度发布管理器

    支持渐进式灰度和快速回滚。
    """

    def __init__(self):
        self._experiments: dict[str, Experiment] = {}
        self._metrics: dict[str, list[MetricPoint]] = {}

    def create_experiment(
        self,
        experiment_id: str,
        flag_name: str,
        description: str,
        target_percentage: float = 100.0,
        duration_hours: int = 24,
    ) -> Experiment:
        """创建灰度实验"""
        experiment = Experiment(
            id=experiment_id,
            flag_name=flag_name,
            description=description,
            target_percentage=target_percentage,
            start_time=datetime.now(),
            duration_hours=duration_hours,
        )
        self._experiments[experiment_id] = experiment
        return experiment

    def update_experiment(
        self,
        experiment_id: str,
        new_percentage: float,
    ) -> None:
        """更新灰度百分比"""
        experiment = self._experiments.get(experiment_id)
        if experiment:
            experiment.current_percentage = new_percentage
            FeatureFlags._flags[experiment.flag_name].rollout_percentage = new_percentage

    def complete_experiment(
        self,
        experiment_id: str,
        success: bool,
    ) -> None:
        """完成实验"""
        experiment = self._experiments.get(experiment_id)
        if experiment:
            experiment.completed = True
            experiment.success = success
            experiment.end_time = datetime.now()

            if success:
                FeatureFlags.enable(experiment.flag_name, temporary=False)
            else:
                FeatureFlags.disable(experiment.flag_name, temporary=False)

    def record_metric(
        self,
        experiment_id: str,
        metric_name: str,
        value: float,
    ) -> None:
        """记录实验指标"""
        if experiment_id not in self._metrics:
            self._metrics[experiment_id] = []
        self._metrics[experiment_id].append(MetricPoint(
            timestamp=datetime.now(),
            name=metric_name,
            value=value,
        ))

    def get_experiment_status(self, experiment_id: str) -> dict[str, Any]:
        """获取实验状态"""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return {}

        return {
            "id": experiment.id,
            "flag_name": experiment.flag_name,
            "description": experiment.description,
            "target_percentage": experiment.target_percentage,
            "current_percentage": experiment.current_percentage,
            "started_at": experiment.start_time.isoformat(),
            "completed": experiment.completed,
            "success": experiment.success if experiment.completed else None,
            "metrics": self._get_experiment_metrics(experiment_id),
        }

    def _get_experiment_metrics(self, experiment_id: str) -> dict[str, Any]:
        """获取实验指标汇总"""
        metrics = self._metrics.get(experiment_id, [])
        result: dict[str, Any] = {}

        for point in metrics:
            if point.name not in result:
                result[point.name] = {"values": [], "count": 0, "sum": 0.0}
            result[point.name]["values"].append(point.value)
            result[point.name]["count"] += 1
            result[point.name]["sum"] += point.value

        for name, data in result.items():
            if data["count"] > 0:
                data["avg"] = data["sum"] / data["count"]

        return result


@dataclass
class Experiment:
    """灰度实验"""
    id: str
    flag_name: str
    description: str
    target_percentage: float
    current_percentage: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    duration_hours: int = 24
    completed: bool = False
    success: bool = False


@dataclass
class MetricPoint:
    """指标点"""
    timestamp: datetime
    name: str
    value: float


_global_rollout_manager: RolloutManager | None = None


def get_rollout_manager() -> RolloutManager:
    """获取全局灰度管理器"""
    global _global_rollout_manager
    if _global_rollout_manager is None:
        _global_rollout_manager = RolloutManager()
    return _global_rollout_manager
