"""
安全申诉处理器
"""

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...core.agent import Agent

logger = logging.getLogger(__name__)

class SafetyHandler:
    def __init__(self, agent: "Agent"):
        self.agent = agent

    async def handle(self, tool_name: str, params: dict[str, Any]) -> str:
        if tool_name == "submit_safety_appeal":
            return await self._handle_appeal(params)
        return f"Unknown tool: {tool_name}"

    async def _handle_appeal(self, params: dict[str, Any]) -> str:
        target = params.get("target_action", "")
        reason = params.get("necessity_reasoning", "")
        mitigation = params.get("mitigation_measures", "")

        # 记录到审计日志
        logger.warning(f"[SafetyAppeal] Target: {target}")
        logger.warning(f"[SafetyAppeal] Reason: {reason}")
        logger.warning(f"[SafetyAppeal] Mitigation: {mitigation}")

        # 使用本 Agent 的 ask_user 机制请求真实确认
        # 构建一个友好的提示供用户裁决
        prompt = (
            f"🚨 **安全申诉请求**\n\n"
            f"Agent 试图执行以下被拦截的操作：\n`{target}`\n\n"
            f"**申诉理由**：\n{reason}\n\n"
            f"**安全承诺**：\n{mitigation}\n\n"
            f"请问是否允许本次操作？(此授权仅对本次任务有效)"
        )

        # 通过 Agent 状态机发起中断
        from ...core.agent_state import TaskStatus
        if self.agent.agent_state and self.agent.agent_state.current_task:
            # 记录申诉数据到任务元数据，以便用户回复后能找回
            self.agent.agent_state.current_task.metadata["pending_appeal"] = params

        # 委托给核心 ask_user 逻辑
        # 注意：此处返回的消息会被 LLM 看到，告诉它正在等待用户审核。
        return (
            "[SYSTEM] 安全申诉已提交，正在等待用户审核。请保持静默，不要重复尝试被拦截的操作。"
            "用户确认后，系统会自动通知你继续。"
        )

def create_handler(agent: "Agent"):
    handler = SafetyHandler(agent)
    return handler.handle
