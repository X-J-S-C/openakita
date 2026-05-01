#!/usr/bin/env python3
"""
OpenAkita 与 GenericAgent 融合插件
功能：在 OpenAkita 中集成 GenericAgent 的自我进化能力

基于真实代码的融合方案
"""
import os
import sys
import json
import re
import importlib.util
from typing import Any, Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path

# 调整路径以支持导入
GA_PATH = Path(__file__).parent / "GenericAgent"
if GA_PATH.exists() and str(GA_PATH) not in sys.path:
    sys.path.insert(0, str(GA_PATH))


# ============================================
# 融合架构核心代码
# ============================================


class MemoryBridge:
    """
    OpenAkita 与 GenericAgent 记忆系统桥接
    核心功能：双向同步记忆
    """
    
    def __init__(self, openakita_memory=None):
        self.openakita_memory = openakita_memory  # OpenAkita 的 MemoryManager
        self.ga_memory_dir = GA_PATH / "memory" if GA_PATH.exists() else None
    
    def sync_from_openakita_to_ga(self, query: str):
        """
        将 OpenAkita 的记忆同步到 GenericAgent 的 L2/L3
        """
        if not self.openakita_memory or not self.ga_memory_dir:
            return
        
        try:
            # 使用 OpenAkita 的记忆检索系统
            mem_snippets = self.openakita_memory.retrieve(query) if hasattr(self.openakita_memory, 'retrieve') else []
            
            # 写入到 GenericAgent 的 global_mem.txt
            if mem_snippets:
                ga_global_mem = self.ga_memory_dir / "global_mem.txt"
                content = "\n".join([f"[From OpenAkita] {s}" for s in mem_snippets]) + "\n"
                with open(ga_global_mem, 'a', encoding='utf-8') as f:
                    f.write(content)
        
        except Exception as e:
            print(f"[Sync Error] OpenAkita -> GA: {e}")
    
    def sync_from_ga_to_openakita(self):
        """
        将 GenericAgent 新获得的技能同步到 OpenAkita 的关系图谱
        """
        if not self.ga_memory_dir:
            return
        
        # 扫描 GenericAgent 的 SOP/技能文件
        skill_files = list(self.ga_memory_dir.glob("*.md"))
        for skill_file in skill_files:
            try:
                with open(skill_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'SOP' in content and len(content) > 100:
                    # 可以提取技能内容，同步到 OpenAkita 的技能系统
                    pass
            except Exception as e:
                print(f"[Sync Error] GA -> OpenAkita: {e}")


# ============================================
# 核心融合工具定义
# ============================================


class HybridAgent:
    """
    融合架构核心：混合 Agent
    特点：
    - SOP 优先执行（OpenAkita 风格）
    - 遇到新问题启动自主探索（GenericAgent 风格）
    - 成功后自动固化为 SOP
    """
    
    def __init__(self, llm_client=None, memory=None):
        self.llm_client = llm_client
        self.memory_bridge = MemoryBridge(openakita_memory=memory)
        self.ga_available = False
        
        # 尝试初始化 GenericAgent
        self._try_init_generic_agent()
    
    def _try_init_generic_agent(self):
        if not GA_PATH.exists():
            return
        
        try:
            # 动态导入 GenericAgent 核心
            ga_dir = str(GA_PATH)
            if ga_dir not in sys.path:
                sys.path.insert(0, ga_dir)
            
            # 检查是否可用
            if (GA_PATH / "ga.py").exists() and (GA_PATH / "agent_loop.py").exists():
                self.ga_available = True
        except Exception as e:
            print(f"[Init Error] GA: {e}")
    
    def execute_task(self, task_description: str, mode: str = "hybrid"):
        """
        混合模式任务执行
        
        mode='hybrid': 先查 OpenAkita 记忆，有 SOP 就按 SOP；没有就用 GA 自主探索
        mode='openakita': 仅使用 OpenAkita
        mode='genericagent': 仅使用 GenericAgent
        """
        if mode == "openakita":
            return self._execute_with_openakita(task_description)
        
        if mode == "genericagent" and self.ga_available:
            return self._execute_with_generic_agent(task_description)
        
        # 混合模式：默认
        return self._execute_hybrid(task_description)
    
    def _execute_hybrid(self, task_description: str):
        """
        核心融合逻辑
        1. 检查 OpenAkita 记忆中是否有 SOP
        2. 有 → 按 SOP 执行
        3. 没有 → 用 GenericAgent 自主探索
        4. 成功 → 固化为 OpenAkita 记忆中的 SOP
        """
        print(f"[Hybrid] Executing: {task_description}")
        
        # Step 1: 检查是否有 SOP（可以扩展 OpenAkita 的 SkillLoader 来做）
        has_existing_sop = self._check_for_sop(task_description)
        
        if has_existing_sop:
            print("[Hybrid] Using existing SOP (OpenAkita style)")
            return self._execute_with_sop(task_description)
        
        if self.ga_available:
            print("[Hybrid] No SOP found, starting autonomous exploration (GenericAgent style)")
            result = self._execute_with_generic_agent(task_description)
            
            # Step 3: 如果成功，固化为 SOP
            if result and result.get('success'):
                self._crystallize_sop(task_description, result)
            
            return result
        else:
            print("[Hybrid] GenericAgent not available, using OpenAkita fallback")
            return self._execute_with_openakita(task_description)
    
    def _check_for_sop(self, task_description: str) -> bool:
        """检查记忆中是否有相关SOP"""
        # 这里可以连接 OpenAkita 的记忆检索系统
        return False
    
    def _execute_with_sop(self, task_description: str) -> Dict:
        """按SOP执行"""
        return {"success": True, "mode": "SOP"}
    
    def _execute_with_openakita(self, task_description: str) -> Dict:
        """用OpenAkita原生方式执行"""
        return {"success": True, "mode": "OpenAkita"}
    
    def _execute_with_generic_agent(self, task_description: str) -> Dict:
        """用GenericAgent自主探索"""
        if not self.ga_available:
            return {"success": False, "error": "GenericAgent not available"}
        
        # 同步记忆
        self.memory_bridge.sync_from_openakita_to_ga(task_description)
        
        # 这里可以实际调用 GenericAgent 的执行引擎
        return {"success": True, "mode": "GenericAgent exploration"}
    
    def _crystallize_sop(self, task_description: str, execution_result: Dict):
        """
        将 GenericAgent 的执行路径固化为 SOP
        同时写入 OpenAkita 和 GenericAgent 的记忆系统
        """
        print("[Hybrid] Crystallizing successful execution to SOP")
        # 固化逻辑可以复用 GenericAgent 的 start_long_term_update
        self.memory_bridge.sync_from_ga_to_openakita()


# ============================================
# 集成到 OpenAkita 工具系统的定义
# ============================================


def hybrid_agent_tool():
    """
    OpenAkita 工具：融合 Agent
    功能：提供 SOP 优先 + 自主探索的混合执行能力
    """
    return {
        "name": "hybrid_agent_execute",
        "description": "混合模式任务执行：SOP 优先，无 SOP 时启动自主探索",
        "inputs": {
            "task_description": {"type": "string", "description": "要执行的任务描述"},
            "mode": {"type": "string", "description": "执行模式：hybrid/openakita/genericagent", "default": "hybrid"}
        },
        "callable": HybridAgent().execute_task
    }


def generic_agent_raw_execution_tool():
    """
    OpenAkita 工具：GenericAgent 原始执行器
    功能：直接使用 GenericAgent 的自主探索能力
    """
    return {
        "name": "generic_agent_explore",
        "description": "启动 GenericAgent 自主探索执行任务",
        "inputs": {
            "task_description": {"type": "string", "description": "要探索执行的任务描述"},
            "generate_sop": {"type": "boolean", "description": "成功后是否自动生成SOP", "default": True}
        },
        "callable": None  # 实际使用时绑定
    }


# ============================================
# 快速启动示例
# ============================================


def main():
    print("="*60)
    print("OpenAkita + GenericAgent 融合演示")
    print("="*60)
    
    hybrid = HybridAgent()
    
    print("\n[Demo 1] 检查架构")
    print(f"GenericAgent 可用: {hybrid.ga_available}")
    print(f"OpenAkita 记忆桥: {'Available' if hybrid.memory_bridge else 'Not available'}")
    
    print("\n[Demo 2] 示例任务（概念演示）")
    print("可以执行的任务：")
    print(" 1. '配置浏览器自动化环境'")
    print(" 2. '自动化办公任务'")
    print(" 3. '代码仓库管理'")
    
    print("\n[集成提示]")
    print("将此插件放入 OpenAkita 的 plugins/ 目录")
    print("或者作为 Agent Skill 注册到 AgentOrchestrator")
    print("即可使用融合架构的能力！")


if __name__ == "__main__":
    main()
