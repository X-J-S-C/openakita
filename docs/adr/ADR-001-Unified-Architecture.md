# ADR-001: 统一演进架构 (Unified Evolution Architecture)

## 状态
提议中 (Proposed)

## 背景
OpenAkita 目前拥有强大的多通道接入、丰富的工具库和三层记忆系统，但在“自我进化”和“架构解耦”方面仍有提升空间。GenericAgent 展现了极致压缩的内核以及基于“技能结晶”的自我成长能力。为了融合两者的优势，我们需要一套基于“端口与适配器”（六边形架构）的统一准则。

## 决策
我们将采用以下架构准则进行深度重构：

### 1. 核心内核 (The Kernel)
- **内核定义**：内核（Core Engine）仅负责 Agent 的基本生命周期管理、状态流转（ReAct 循环）和事件分发。
- **解耦要求**：内核不直接依赖具体的 LLM 供应商、不直接操作文件系统、不感知特定的 IM 平台。

### 2. 接口契约 (SPI/Interfaces)
- **BaseKernel**: 定义 `run_task`, `pause`, `resume`, `stop`。
- **BaseMemory**: 定义 `query`, `store`, `consolidate`。
- **BaseTool**: 定义 `execute`, `get_definition`。
- **BaseLLM**: 定义 `think`, `stream`。

### 3. 记忆与进化 (Memory & Evolution)
- **结晶器 (Crystallizer)**：作为 Memory 系统的一个特定 Provider，负责将成功的 Trace 转化为结构化的 SOP (SKILL.md)。
- **影子验证 (Shadow Verification)**：引入 `ShadowWorkspace` 适配器，所有新技能在正式入库前必须在沙箱中跑通。

### 4. 数字化映射 (Observability)
- 记忆和思维过程必须通过标准 JSON 格式输出，以便于 `MemoryGraph` 进行多维可视化渲染。

## 后果
- **正面**：系统模块化程度显著提高，核心逻辑更易于测试；具备了类似“数字生命”的自我进化能力。
- **负面**：重构初期工作量大，需要编写大量的抽象接口和适配器代码。
