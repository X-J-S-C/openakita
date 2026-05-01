"""
离线蒸馏数据导出器 (Offline Distillation Exporter)

将 L3 技能 (SOP) 与 L4 任务轨迹 (Trace) 对齐，生成高质量的训练数据集，
为未来本地小模型 (SLM) 的“经验蒸馏”打下基础。
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DistillationExporter:
    """
    负责导出高质量的 (任务-路径-技能) 三元组数据。
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.output_dir = data_dir / "distillation"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_alignment_data(self, task_id: str, task_desc: str, trace: List[Dict], skill_content: str):
        """
        导出一条对齐后的蒸馏样本。
        格式：JSONL，包含 input (task), reasoning (trace_pruned), output (skill_sop)。
        """
        sample = {
            "id": task_id,
            "timestamp": datetime.now().isoformat(),
            "input": task_desc,
            "instruction_trace": self._prune_for_training(trace),
            "target_sop": skill_content
        }

        output_file = self.output_dir / f"dataset_{datetime.now().strftime('%Y%m')}.jsonl"
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

        logger.info(f"[Distillation] Exported 1 sample to {output_file}")

    def _prune_for_training(self, trace: List[Dict]) -> List[Dict]:
        """为模型训练进一步修剪 Trace，去除不必要的元数据。"""
        train_trace = []
        for it in trace:
            # 只保留工具名和最简化的输入输出
            step = {
                "t": [ { "n": tc.get("name"), "i": tc.get("input") } for tc in it.get("tool_calls", []) ],
                "o": [ { "r": tr.get("result_content")[:200] } for tr in it.get("tool_results", []) ]
            }
            train_trace.append(step)
        return train_trace
