"""
Markdown-DB 同步引擎

将记忆持久化为人类可读、可被 Git 追踪的 Markdown 文件，
同时同步到 SQLite 数据库以支持高性能检索。
"""

import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from .types import Memory, MemoryType, MemoryPriority, SemanticMemory

logger = logging.getLogger(__name__)

class MarkdownSyncer:
    """
    Markdown 与 数据库 的双向同步引擎。

    层级定义：
    L0: rules/*.md (只读规则)
    L1: triggers.json (触发索引)
    L2: facts.md (验证事实)
    L3: sops/*.md (技能 SOP)
    L4: traces/ (原始轨迹)
    """

    def __init__(self, data_dir: Path, store: Any):
        self.data_dir = data_dir
        self.store = store
        self.l2_path = data_dir / "facts.md"
        self.l3_dir = data_dir / "sops"
        self.l3_dir.mkdir(parents=True, exist_ok=True)

    def sync_all_to_db(self):
        """从 Markdown 加载所有内容并刷新数据库缓存"""
        logger.info("Syncing Markdown memories to Database...")

        # 1. 同步 L2 Facts
        if self.l2_path.exists():
            facts = self._parse_markdown_list(self.l2_path.read_text(encoding="utf-8"))
            for fact in facts:
                mem = SemanticMemory(
                    content=fact['content'],
                    type=MemoryType.FACT,
                    priority=MemoryPriority.LONG_TERM,
                    source="markdown_sync",
                    tags=["l2"]
                )
                self.store.save_semantic(mem, skip_dedup=True)

        # 2. 同步 L3 SOPs
        for sop_file in self.l3_dir.glob("*.md"):
            content = sop_file.read_text(encoding="utf-8")
            # 提取描述作为索引
            description = self._extract_sop_description(content)
            mem = SemanticMemory(
                content=f"SOP: {sop_file.stem} - {description}",
                type=MemoryType.EXPERIENCE,
                priority=MemoryPriority.PERMANENT,
                source="markdown_sync",
                metadata={"file_path": str(sop_file)},
                tags=["l3", "sop"]
            )
            self.store.save_semantic(mem, skip_dedup=True)

    def add_l2_fact(self, content: str):
        """向 L2 facts.md 添加一条事实并同步到 DB"""
        if not self.l2_path.exists():
            self.l2_path.write_text("# L2 Verified Facts\n\n", encoding="utf-8")

        with open(self.l2_path, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            f.write(f"- [{timestamp}] {content}\n")

        # 同步到 DB
        mem = SemanticMemory(
            content=content,
            type=MemoryType.FACT,
            priority=MemoryPriority.LONG_TERM,
            source="manual_add",
            tags=["l2"]
        )
        self.store.save_semantic(mem)

    def _parse_markdown_list(self, content: str) -> List[Dict]:
        """解析 Markdown 列表项"""
        items = []
        for line in content.splitlines():
            match = re.match(r"^[*-]\s+(?:\[.*?\]\s+)?(.*)$", line.strip())
            if match:
                items.append({"content": match.group(1)})
        return items

    def _extract_sop_description(self, content: str) -> str:
        """从 SOP 文件中提取简介"""
        # 尝试寻找 Description: xxx 或第一行非标题行
        match = re.search(r"Description:\s*(.*)", content, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
        return lines[0] if lines else "No description"
