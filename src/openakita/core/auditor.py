"""
AuditorNode - 启发式审计员

负责对 Agent 的每一步操作进行“安全预审”和“事后验证”。
核心原则：
1. 风险分级：根据工具破坏性决定审计深度。
2. 申诉闭环：允许 Agent 对误判进行申诉。
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    L1_INFO = "info"      # 读取、查询 - 直通
    L2_MODERATE = "mod"   # 修改文件、普通命令 - 影子执行 + 异步审计
    L3_CRITICAL = "crit"  # 系统配置、删除操作 - 同步阻塞审计

@dataclass
class AuditResult:
    allowed: bool
    risk_level: RiskLevel
    reason: str = ""
    requires_defense: bool = False

class AuditorNode:
    """审计节点。"""

    def __init__(self, l0_rules: Any):
        self.l0_rules = l0_rules

    def pre_audit(self, tool_name: str, tool_input: dict) -> AuditResult:
        """执行前预审。"""
        # 1. 识别风险等级
        level = self._classify_risk(tool_name, tool_input)

        # 2. 命中 L0 规则检查
        # 借用 permission 模块的 evaluate 逻辑
        from .permission import evaluate, _tool_to_permission

        perm = _tool_to_permission(tool_name)
        pattern = "*"
        if "path" in tool_input:
            pattern = str(tool_input["path"])

        rule = evaluate(perm, pattern, self.l0_rules)

        if rule.action == "deny":
            return AuditResult(
                allowed=False,
                risk_level=level,
                reason=f"L0 Rule Violation: {rule.permission} on {rule.pattern}",
                requires_defense=True
            )

        return AuditResult(allowed=True, risk_level=level)

    def _classify_risk(self, tool_name: str, tool_input: dict) -> RiskLevel:
        """简单的启发式风险分类。"""
        if tool_name in ("read_file", "list_directory", "web_search", "news_search"):
            return RiskLevel.L1_INFO

        if tool_name in ("delete_file", "browser_execute_js") or "rm " in str(tool_input.get("command", "")):
            return RiskLevel.L3_CRITICAL

        return RiskLevel.L2_MODERATE

    async def handle_appeal(self, defense: str, original_task: str) -> bool:
        """处理 Agent 的申诉（DefenseReasoning）。
        目前阶段：记录日志并请求用户裁决。
        """
        logger.warning(f"[Auditor] Received SafetyAppeal for task: {original_task[:100]}")
        logger.warning(f"[Auditor] Defense: {defense}")
        # 在真实 IM/CLI 环境中，此处会调用 ask_user
        return False # 默认维持拦截，等待人工干预
