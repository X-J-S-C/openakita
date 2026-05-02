# Akita-Evo 架构升级说明 (Phase 1-3)

恭喜！您的 OpenAkita 已成功升级为具备 **“数字化自愈能力”** 的演进架构。本次升级将 GenericAgent 的极简进化理念与 OpenAkita 的工程深度进行了完美融合。

## 1. 影子工作区 (Shadow Workspace) — 常态化与回溯
现在，Agent 的所有写文件、修改配置操作都默认在影子路径执行。
- **可视化回溯**：您可以使用 `trace_file_operations` 工具查看 Agent 对文件的每一次“增删改减”。
- **Git 级安全性**：即使 Agent 修改错了文件，您也可以在提交前进行拦截或回滚。
- **操作树形式**：
  ```
  📂 Shadow Workspace Trace: task-xxx
  ├── [WRITE_FILE] config.json
  ├── [EDIT_FILE] main.py
  └── [DELETE_FILE] old_cache.tmp
  ```

## 2. 结晶器自愈闭环 (Self-Healing Crystallizer)
Agent 不再只是机械地记录记忆，它现在会**“复盘”**。
- **自主演练**：生成的技能 SOP (SKILL.md) 会自动在影子工作区运行。
- **自动修正**：如果 SOP 步骤逻辑不通或执行报错，Agent 会自动调用“自愈专家”模型进行修正，直到技能可以稳定复现。

## 3. 记忆系统 3D 可视化 (Dashboard)
现在调用 `visualize_memory_graph` 将不再只是输出 Mermaid 代码，而是生成一张精美的 **PNG 数字化脑图**（存放于 `data/plots/`）。
- **包含维度**：记忆类型分布饼图、优先级分布、总览统计、知识图谱网络、以及最近的系统活动。

## 4. 架构解耦 (The Kernel)
底层内核已实现标准 SPI 化。这意味着未来的扩展将更加模块化，就像“插拔乐高”一样简单。

---
*安全、进化、主权 —— OpenAkita Akita-Evo*
