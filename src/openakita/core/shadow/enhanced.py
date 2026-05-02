import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..kernel.base import BaseShadowWorkspace

logger = logging.getLogger(__name__)

class EnhancedShadowWorkspace(BaseShadowWorkspace):
    """
    增强版影子工作区。
    支持操作记录、路径重定向及类似 Git 的变更追踪。
    """

    def __init__(self, base_path: Path, task_id: str):
        self.base_path = base_path.resolve()
        self.task_id = task_id
        # 使用项目根目录下的 .openakita/shadow 存储影子文件
        self.shadow_root = self.base_path / ".openakita" / "shadow" / task_id
        self.history: List[Dict[str, Any]] = []
        self._is_active = False

    async def __aenter__(self):
        if not self.shadow_root.exists():
            self.shadow_root.mkdir(parents=True, exist_ok=True)
        self._is_active = True
        logger.info(f"[EnhancedShadow] Workspace active at {self.shadow_root}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._is_active = False
        logger.debug(f"[EnhancedShadow] Workspace deactivated for {self.task_id}")

    def resolve_path(self, path_str: str) -> Path:
        """
        核心逻辑：将任何文件路径请求拦截并重定向到影子工作区。
        """
        p = Path(path_str)
        # 如果是绝对路径，尝试计算相对于 base_path 的相对路径
        if p.is_absolute():
            try:
                rel = p.relative_to(self.base_path)
                return self.shadow_root / rel
            except ValueError:
                # 如果绝对路径不在 base_path 下，为了安全重定向到影子根目录下的文件名
                return self.shadow_root / p.name

        # 相对路径直接拼接
        return self.shadow_root / p

    def record_operation(self, op: str, path: str, **params):
        """记录操作历史，为可视化树状图提供数据"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "op": op,
            "path": path,
            "params": params
        })
        logger.debug(f"[EnhancedShadow] Recorded op: {op} on {path}")

    async def commit(self):
        """将影子变更同步到物理磁盘"""
        logger.info(f"[EnhancedShadow] Committing changes for {self.task_id}")
        if not self.shadow_root.exists():
            return

        for item in self.shadow_root.rglob("*"):
            if item.is_file():
                rel = item.relative_to(self.shadow_root)
                target = self.base_path / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
        logger.info("[EnhancedShadow] Commit success")

    async def rollback(self):
        """丢弃影子变更"""
        if self.shadow_root.exists():
            shutil.rmtree(self.shadow_root)
        self.history.clear()
        logger.info(f"[EnhancedShadow] Rollback complete for {self.task_id}")

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history

    def generate_visual_tree(self) -> str:
        """生成操作树的可视化字符串"""
        if not self.history:
            return "No operations recorded."

        lines = [f"📂 Shadow Workspace Trace: {self.task_id}"]
        for i, entry in enumerate(self.history):
            prefix = "└── " if i == len(self.history) - 1 else "├── "
            lines.append(f"{prefix}[{entry['op'].upper()}] {entry['path']}")
        return "\n".join(lines)
