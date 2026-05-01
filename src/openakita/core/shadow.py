"""
影子工作区 (Shadow Workspace)

实现“执行-验证-合并”的影子执行模式：
1. 创建临时隔离目录 (Clone-on-demand)
2. 在影子环境中执行破坏性工具
3. 验证通过后同步回主环境
"""

import os
import shutil
import logging
import asyncio
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

class ShadowWorkspace:
    """
    影子工作区管理器。

    使用示例:
    async with ShadowWorkspace(base_path=Path.cwd()) as sw:
        await sw.run_tool("write_file", {"path": "test.txt", "content": "hello"})
        if await sw.verify():
            await sw.commit()
    """

    def __init__(self, base_path: Path, task_id: str):
        self.base_path = base_path.resolve()
        self.task_id = task_id
        self.shadow_path = base_path / ".openakita" / "shadow" / task_id
        self._is_active = False

    async def __aenter__(self):
        """进入影子模式：准备目录"""
        if not self.shadow_path.exists():
            self.shadow_path.mkdir(parents=True, exist_ok=True)
        self._is_active = True
        logger.info(f"[Shadow] Workspace initialized at {self.shadow_path}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出影子模式：清理环境"""
        self._is_active = False
        # 默认不自动删除，留待任务最终 finalize 清理或 debug
        logger.debug(f"[Shadow] Exited shadow mode for {self.task_id}")

    def resolve_path(self, original_path: str) -> Path:
        """将主环境路径映射到影子环境路径。"""
        p = Path(original_path)
        if p.is_absolute():
            try:
                rel = p.relative_to(self.base_path)
                return self.shadow_path / rel
            except ValueError:
                # 不在 base_path 下的绝对路径，为了安全，强制重定向到影子根目录
                return self.shadow_path / p.name
        return self.shadow_path / p

    async def commit(self):
        """将影子环境中的所有变更同步回主环境。"""
        logger.info(f"[Shadow] Committing changes from {self.task_id} to main workspace")
        # 简单递归拷贝覆盖
        for item in self.shadow_path.rglob("*"):
            if item.is_file():
                rel = item.relative_to(self.shadow_path)
                target = self.base_path / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
        logger.info("[Shadow] Commit complete.")

    async def rollback(self):
        """丢弃变更。"""
        if self.shadow_path.exists():
            shutil.rmtree(self.shadow_path)
        logger.info(f"[Shadow] Changes discarded for {self.task_id}")

def is_shadow_eligible(tool_name: str) -> bool:
    """判断工具是否应当在影子环境中执行。"""
    SHADOW_TOOLS = {
        "write_file",
        "edit_file",
        "replace_in_file",
        "create_file",
        "delete_file",
        "run_shell",
        "run_powershell"
    }
    return tool_name in SHADOW_TOOLS
