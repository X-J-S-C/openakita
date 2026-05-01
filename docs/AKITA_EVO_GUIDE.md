# Akita-Evo 升级操作指南 (Phase 2)

本指南旨在指导用户如何使用 Akita-Evo 升级包中引入的高级安全审计与自进化特性。

## 1. 安全申诉机制 (Safety Appeal)
当 Agent 的操作被 **AuditorNode** 拦截（例如试图访问受保护的系统目录）时，Agent 不再直接报错退出，而是可以发起结构化申诉。

### 操作流程：
1. Agent 发现操作被拦截，自动调用 `submit_safety_appeal`。
2. 系统会在您的交互界面（CLI/IM）显示申诉详情：
   - **目标操作**：试图执行的具体指令。
   - **必要性**：Agent 解释为什么完成您的任务必须执行此操作。
   - **缓解措施**：Agent 承诺采取的安全保护（如：在影子目录执行、只读访问等）。
3. **用户裁决**：您可以回复“同意”或“拒绝”。同意后，Agent 将获得该操作的一次性授权。

## 2. 技能演练验证 (Dry-Run Verification)
为了确保自结晶出的 SOP 质量，我们引入了“演练”机制。

- **配置项**：在 `.env` 中设置 `EVOLUTION_DRY_RUN=true`。
- **效果**：技能结晶后，Agent 会在影子工作区自动执行 Instructions。只有通过演练的技能，其 Markdown 头部才会标记为 `#verified`。

## 3. 记忆图谱可视化
您可以随时查看 AI 记忆的组织架构，识别哪些是原始事实，哪些是演化出的技能。

- **使用工具**：调用 `visualize_memory_graph()`。
- **输出**：系统将返回一段 **Mermaid** 拓扑代码。
- **查看方式**：您可以将代码粘贴至 [Mermaid Live Editor](https://mermaid.live/) 或直接让支持 Mermaid 渲染的客户端展示。

## 4. 离线蒸馏管线 (SLM Distillation)
Akita-Evo 正在为您未来的“本地化”做准备。

- **数据存储**：所有成功的 (任务 -> 轨迹 -> 技能) 三元组都会自动导出至 `data/distillation/dataset_YYYYMM.jsonl`。
- **用途**：这些高质量数据可直接用于微调（Fine-tune）您自己的本地小模型，使其在不联网的情况下也能拥有接近云端大模型的 SOP 执行能力。

---
*安全、进化、主权 —— OpenAkita Akita-Evo*
