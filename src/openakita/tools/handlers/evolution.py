"""
自进化处理器
"""

import os
import shutil
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...core.agent import Agent

logger = logging.getLogger(__name__)

class EvolutionHandler:
    def __init__(self, agent: "Agent"):
        self.agent = agent
        self.pending_dir = Path("data/evolution/pending")
        self.official_dir = Path("skills") # 默认技能目录

    async def handle(self, tool_name: str, params: dict[str, Any]) -> str:
        if tool_name == "list_pending_skills":
            return self._list_pending()
        elif tool_name == "approve_crystallized_skill":
            return await self._approve(params.get("skill_name", ""))
        elif tool_name == "reject_crystallized_skill":
            return self._reject(params.get("skill_name", ""))
        return f"Unknown tool: {tool_name}"

    def _list_pending(self) -> str:
        if not self.pending_dir.exists():
            return "当前没有待审核的技能。"

        skills = [d.name for d in self.pending_dir.iterdir() if d.is_dir()]
        if not skills:
            return "当前没有待审核的技能。"

        res = "📋 **待审核技能列表**：\n"
        for s in skills:
            res += f"- `{s}`\n"
        res += "\n你可以调用 `read_file` 查看 `SKILL.md` 内容，或调用 `approve_crystallized_skill` 通过审核。"
        return res

    async def _approve(self, skill_name: str) -> str:
        src = self.pending_dir / skill_name
        dest = self.official_dir / skill_name

        if not src.exists():
            return f"❌ 找不到待审核技能: {skill_name}"

        try:
            self.official_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))

            # 触发 Agent 内部的技能重载
            self.agent.propagate_skill_change(action="approve", rescan=True)

            logger.info(f"[Evolution] Approved skill: {skill_name}")
            return f"✅ 技能 `{skill_name}` 已通过审核，并正式存入技能库。"
        except Exception as e:
            return f"❌ 审核操作失败: {e}"

    def _reject(self, skill_name: str) -> str:
        src = self.pending_dir / skill_name
        if not src.exists():
            return f"❌ 找不到待审核技能: {skill_name}"

        try:
            shutil.rmtree(src)
            return f"✅ 已拒绝并删除待审核技能: {skill_name}"
        except Exception as e:
            return f"❌ 操作失败: {e}"

def create_handler(agent: "Agent"):
    handler = EvolutionHandler(agent)
    return handler.handle
