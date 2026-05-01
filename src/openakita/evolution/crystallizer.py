"""
成功经验结晶器 (Success Crystallizer)

功能：
- 监听并分析成功的 ReAct Trace
- 提取核心执行路径（SOP）
- 自动生成符合 Agent Skills 规范的 SKILL.md
- 实现 GenericAgent 风格的“自生成技能树”能力
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import settings
from ..core.brain import Brain
from ..core.response_handler import strip_thinking_tags

logger = logging.getLogger(__name__)

@dataclass
class CrystallizationResult:
    """结晶结果"""
    success: bool
    skill_name: str
    skill_dir: str | None = None
    skill_content: str | None = None
    error: str | None = None

class SuccessCrystallizer:
    """
    成功经验结晶器

    将成功的任务执行 Trace 转化为持久化的技能。
    """

    def __init__(self, brain: Brain, skills_dir: Path | None = None):
        self.brain = brain
        self.skills_dir = skills_dir or settings.skills_path
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    async def crystallize(self, task_description: str, react_trace: list[dict]) -> CrystallizationResult:
        """
        从成功 Trace 中提炼技能

        Args:
            task_description: 原始任务描述
            react_trace: ReAct 循环追踪数据
        """
        if not react_trace:
            return CrystallizationResult(success=False, skill_name="", error="Trace 为空")

        logger.info(f"[Crystallizer] 开始为任务结晶技能: {task_description[:50]}...")

        # 1. 预处理 Trace：移除冗余信息，仅保留成功的工具调用及其核心输入输出
        clean_trace = self._preprocess_trace(react_trace)

        try:
            # 2. 调用 LLM 生成 SKILL.md 内容
            skill_info = await self._generate_skill_definition(task_description, clean_trace)

            skill_name = skill_info.get("name", "auto-generated-skill")
            skill_content = skill_info.get("content", "")

            if not skill_content:
                return CrystallizationResult(success=False, skill_name=skill_name, error="生成内容为空")

            # 3. 确定存储路径
            safe_name = self._normalize_skill_name(skill_name)
            skill_path = self.skills_dir / safe_name
            skill_path.mkdir(exist_ok=True)

            # 4. 写入文件
            (skill_path / "SKILL.md").write_text(skill_content, encoding="utf-8")

            logger.info(f"[Crystallizer] 技能结晶成功: {safe_name} -> {skill_path}")

            return CrystallizationResult(
                success=True,
                skill_name=safe_name,
                skill_dir=str(skill_path),
                skill_content=skill_content
            )

        except Exception as e:
            logger.error(f"[Crystallizer] 结晶过程出错: {e}")
            return CrystallizationResult(success=False, skill_name="", error=str(e))

    def _preprocess_trace(self, trace: list[dict]) -> list[dict]:
        """精简 Trace，只保留关键步骤"""
        processed = []
        for it in trace:
            # 只保留有工具调用的轮次
            if not it.get("tool_calls"):
                continue

            clean_it = {
                "iteration": it.get("iteration"),
                "tools": []
            }

            results_map = {r.get("tool_use_id"): r for r in it.get("tool_results", [])}

            for tc in it.get("tool_calls", []):
                tid = tc.get("id")
                res = results_map.get(tid, {})

                # 过滤掉失败的工具调用（除非是必要的探索）
                if res.get("is_error"):
                    continue

                # 精简输出内容，避免 LLM 上下文爆炸
                content = str(res.get("result_content", ""))
                if len(content) > 1000:
                    content = content[:500] + "...(truncated)..." + content[-500:]

                clean_it["tools"].append({
                    "name": tc.get("name"),
                    "input": tc.get("input"),
                    "output": content
                })

            if clean_it["tools"]:
                processed.append(clean_it)

        return processed

    async def _generate_skill_definition(self, task: str, trace: list[dict]) -> dict:
        """调用 LLM 生成 SKILL.md"""
        # 优先使用结晶专用强模型 DeepSeek-V4-Pro (如果配置了)
        evo_model = getattr(settings, "evolution_model", "deepseek-v4-pro")

        prompt = f"""你是一个高级 AI 架构师，擅长将零散的行动轨迹结晶为标准化的 SOP。
请分析以下成功的任务执行记录，提炼出一个高复用性的 `SKILL.md` 技能定义。

### 原始任务
{task}

### 成功执行路径 (已剔除失败尝试)
{json.dumps(trace, ensure_ascii=False, indent=2)}

### 结晶规范
1. **抽象化**：从具体参数中提取模式。例如把 "git clone https://repo.com" 抽象为 "获取源码仓库"。
2. **SKILL.md 结构**：
   - `name`: 机器可读的唯一标识（kebab-case）。
   - `description`: 简单说明此技能解决什么问题。
   - `instructions`: 核心部分。列出关键步骤、必要的工具调用、以及在这个任务中发现的“避坑指南”。
3. **验证点**：指出在执行过程中，如何判断每一步是否成功。

请直接返回 JSON 格式：
{{
  "name": "skill-id",
  "display_name": "中文名称",
  "description": "简要描述",
  "content": "完整的 Markdown 内容"
}}
"""

        response = await self.brain.think(prompt, system="你是一个技能结晶专家，严禁废话，只输出 JSON。", model_override=evo_model)

        # 解析 JSON
        try:
            content = strip_thinking_tags(response.content)
            # 尝试定位 JSON 块
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                return json.loads(match.group())
            return json.loads(content)
        except Exception:
            return {
                "name": "crystallized-skill-" + datetime.now().strftime("%H%M%S"),
                "content": response.content
            }

    def _normalize_skill_name(self, name: str) -> str:
        """标准化技能名称"""
        name = name.lower().strip()
        name = re.sub(r"[^a-z0-9-]", "-", name)
        name = re.sub(r"-+", "-", name)
        return name.strip("-")
