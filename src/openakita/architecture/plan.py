"""
规划模块

定义任务规划和执行计划相关的数据结构。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """计划步骤状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStrategy(Enum):
    """规划策略"""
    RALPH = "ralph"           # Ralph Wiggum 永不放弃
    REACT = "react"           # ReAct (Reasoning + Acting)
    TOT = "tot"               # Tree of Thoughts
    REFLEXION = "reflexion"   # Reflexion 自反思
    AUTO = "auto"             # 自动选择


@dataclass
class Plan:
    """执行计划"""
    id: str
    goal: str
    steps: list["PlanStep"] = field(default_factory=list)
    strategy: PlanStrategy = PlanStrategy.RALPH
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: "PlanStep") -> None:
        """添加步骤"""
        self.steps.append(step)
        self.updated_at = datetime.now()

    def get_step(self, step_id: str) -> "PlanStep | None":
        """获取步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def remove_step(self, step_id: str) -> bool:
        """移除步骤"""
        for i, step in enumerate(self.steps):
            if step.id == step_id:
                self.steps.pop(i)
                self.updated_at = datetime.now()
                return True
        return False

    def reorder_steps(self, step_ids: list[str]) -> bool:
        """重新排序步骤"""
        step_map = {s.id: s for s in self.steps}
        new_steps = []

        for sid in step_ids:
            if sid in step_map:
                new_steps.append(step_map[sid])
            else:
                return False

        self.steps = new_steps
        self.updated_at = datetime.now()
        return True

    @property
    def is_complete(self) -> bool:
        """是否全部完成"""
        return len(self.steps) > 0 and all(
            s.status == StepStatus.COMPLETED for s in self.steps
        )

    @property
    def is_failed(self) -> bool:
        """是否失败"""
        return any(s.status == StepStatus.FAILED for s in self.steps)

    @property
    def progress(self) -> float:
        """完成进度"""
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)
        return completed / len(self.steps)

    @property
    def next_pending_step(self) -> "PlanStep | None":
        """获取下一个待执行步骤"""
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                return step
        return None

    def get_failed_steps(self) -> list["PlanStep"]:
        """获取失败的步骤"""
        return [s for s in self.steps if s.status == StepStatus.FAILED]

    def get_completed_steps(self) -> list["PlanStep"]:
        """获取已完成的步骤"""
        return [s for s in self.steps if s.status == StepStatus.COMPLETED]

    def reset(self) -> None:
        """重置计划"""
        for step in self.steps:
            step.status = StepStatus.PENDING
            step.result = None
            step.error = None
            step.started_at = None
            step.completed_at = None
        self.updated_at = datetime.now()


@dataclass
class PlanStep:
    """计划步骤"""
    id: str
    description: str
    action: str
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: str | None = None
    dependencies: list[str] = field(default_factory=list)
    estimated_duration_ms: float = 0.0
    actual_duration_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        """开始步骤"""
        self.status = StepStatus.IN_PROGRESS
        self.started_at = datetime.now()
        self.retry_count += 1

    def complete(self, result: Any = None) -> None:
        """完成步骤"""
        self.status = StepStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
        if self.started_at:
            self.actual_duration_ms = (
                self.completed_at - self.started_at
            ).total_seconds() * 1000

    def fail(self, error: str) -> None:
        """步骤失败"""
        self.status = StepStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
        if self.started_at:
            self.actual_duration_ms = (
                self.completed_at - self.started_at
            ).total_seconds() * 1000

    def skip(self) -> None:
        """跳过步骤"""
        self.status = StepStatus.SKIPPED
        self.completed_at = datetime.now()

    def can_retry(self) -> bool:
        """是否可以重试"""
        return (
            self.status == StepStatus.FAILED
            and self.retry_count < self.max_retries
        )

    def reset(self) -> None:
        """重置步骤"""
        self.status = StepStatus.PENDING
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None

    @property
    def duration_ms(self) -> float:
        """获取实际执行时长"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        elif self.started_at:
            return (datetime.now() - self.started_at).total_seconds() * 1000
        return 0.0


@dataclass
class PlanEvaluation:
    """计划评估"""
    plan: Plan
    quality_score: float
    feasibility_score: float
    efficiency_score: float
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    estimated_total_duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def overall_score(self) -> float:
        """综合评分"""
        return (
            self.quality_score * 0.4
            + self.feasibility_score * 0.3
            + self.efficiency_score * 0.3
        )

    @property
    def is_acceptable(self) -> bool:
        """是否可接受"""
        return self.overall_score >= 0.6


@dataclass
class PlanTemplate:
    """计划模板"""
    id: str
    name: str
    description: str
    steps: list[str]  # 步骤描述模板
    conditions: dict[str, str] = field(default_factory=dict)  # 条件模板
    metadata: dict[str, Any] = field(default_factory=dict)

    def create_plan(self, goal: str, context: dict[str, Any] | None = None) -> Plan:
        """从模板创建计划"""
        steps = []
        for i, step_desc in enumerate(self.steps, 1):
            desc = step_desc.format(**(context or {}))
            steps.append(PlanStep(
                id=f"{self.id}_step_{i}",
                description=desc,
                action=desc,
            ))

        return Plan(
            id=f"{self.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            goal=goal,
            steps=steps,
        )


class DefaultPlanTemplates:
    """默认计划模板"""

    RESEARCH = PlanTemplate(
        id="research",
        name="调研模板",
        description="通用调研任务模板",
        steps=[
            "收集相关信息",
            "整理和分类信息",
            "分析关键点",
            "总结结论",
        ],
    )

    CODE_REVIEW = PlanTemplate(
        id="code_review",
        name="代码审查模板",
        description="代码审查任务模板",
        steps=[
            "阅读代码",
            "检查代码质量",
            "检查安全性",
            "提供改进建议",
        ],
    )

    TASK_EXECUTION = PlanTemplate(
        id="task_execution",
        name="任务执行模板",
        description="通用任务执行模板",
        steps=[
            "理解任务目标",
            "制定执行计划",
            "执行计划",
            "验证结果",
            "总结报告",
        ],
    )
