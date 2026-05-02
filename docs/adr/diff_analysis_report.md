# OpenAkita & GenericAgent 融合差异分析报告

## 1. 现状对比

| 特性维度 | OpenAkita (1.27.9) | GenericAgent | 融合策略 |
| :--- | :--- | :--- | :--- |
| **内核逻辑** | Ralph Loop (复杂、健壮、含重试分析) | 极简 Seed (3.3K行、高度压缩) | 提取 OpenAkita 的鲁棒性，采用 GenericAgent 的极简接口化设计 |
| **记忆系统** | L0-L4 (Rules, Facts, SOPs, Traces) | 动态技能树 (Skill Tree Growth) | 将技能树生长逻辑并入 L3 SOP 层，实现自动结晶 |
| **网页处理** | Playwright + 多种解析器 | SimpHTML (极致 Token 压缩) | 全面推广 SimpHTML 作为默认网页压缩方案 |
| **执行安全** | AuditorNode (规则拦截) | N/A (侧重于自由演进) | 保留 AuditorNode，并引入影子工作区进行进化前的安全演练 |
| **可视化** | Mermaid 文本输出 | N/A (主要为命令行/日志) | 自研动态图片渲染引擎，实现 3D/多维记忆图谱 |

## 2. 优先并入特性 (Phase 1 & 2)

1.  **自动结晶 (Success Crystallizer)**：任务成功后，自动提炼 SOP 写入 `skills/auto/`。
2.  **影子工作区 (Shadow Workspace)**：提供隔离的路径操作环境，用于进化自测。
3.  **统一内核接口 (Kernel SPI)**：解耦 `Agent` 与 `ReasoningEngine`，支持不同的推理策略切换。

## 3. 架构演进方向
从“命令执行式 Agent”向“自我修正、自我学习型 Agent”演进。
