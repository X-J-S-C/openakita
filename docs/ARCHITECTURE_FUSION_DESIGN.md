# OpenAkita × GenericAgent 融合架构设计

> 版本: 1.0.0
> 日期: 2026-05-01
> 状态: 设计中

---

## 一、融合愿景

将 OpenAkita 的成熟特性（Ralph 永不放充循环、多 IM 通道、插件系统、Skills 生态）与 GenericAgent 的模块化设计（六边形架构、策略模式、可插拔适配器）深度融合，打造一个既稳定可演进、又高度可扩展的 Agent 基础设施。

---

## 二、目标架构：六边形（端口与适配器）

```
                    ┌─────────────────────────────────────────────────────┐
                    │                    应用层 (Application)              │
                    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
                    │  │  CLI Agent  │  │  IM Gateway │  │  API Server │  │
                    │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
                    └─────────┼─────────────────┼─────────────────┼─────────┘
                              │                 │                 │
                    ┌─────────▼─────────────────▼─────────────────▼─────────┐
                    │                      端口层 (Ports)                     │
                    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
                    │  │AgentPort │ │MemoryPort│ │ToolPort  │ │ModelPort │ │
                    │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
                    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
                    │  │SkillPort │ │PlanPort  │ │EvalPort  │ │AuthPort  │ │
                    │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
                    └───────────────────────────────────────────────────────┘
                              │                 │                 │
                    ┌─────────▼─────────────────▼─────────────────▼─────────┐
                    │                      内核层 (Core)                     │
                    │                                                              │
                    │   ┌─────────────────────────────────────────────────┐    │
                    │   │              AgentKernel (Ralph Loop)            │    │
                    │   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────┐ │    │
                    │   │  │ State   │ │ Plan    │ │ Execute │ │Reflect│ │    │
                    │   │  │ Machine │ │ Engine  │ │ Engine  │ │Engine │ │    │
                    │   │  └─────────┘ └─────────┘ └─────────┘ └───────┘ │    │
                    │   └─────────────────────────────────────────────────┘    │
                    │                                                              │
                    │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐   │
                    │   │ Event   │ │ Hooks   │ │ Checkpoint│ │ Observability│  │
                    │   │ Bus     │ │ System  │ │ Manager │ │ Integration │   │
                    │   │ └─────────┘ └─────────┘ └─────────┘ └─────────────┘   │
                    └───────────────────────────────────────────────────────────┘
                              │                 │                 │
                    ┌─────────▼─────────────────▼─────────────────▼─────────────┐
                    │                    适配器层 (Adapters)                   │
                    │                                                              │
                    │  ┌────────────┐ ┌────────────┐ ┌────────────┐            │
                    │  │ OpenAkita  │ │ Generic    │ │ Custom    │            │
                    │  │ Adapter   │ │ Agent      │ │ Adapter   │            │
                    │  │           │ │ Adapter    │ │           │            │
                    │  └────────────┘ └────────────┘ └────────────┘            │
                    │                                                              │
                    │  ┌────────────┐ ┌────────────┐ ┌────────────┐            │
                    │  │ Memory     │ │ Tool      │ │ Model     │             │
                    │  │ Adapters   │ │ Adapters  │ │ Adapters  │             │
                    │  └────────────┘ └────────────┘ └────────────┘            │
                    └───────────────────────────────────────────────────────────┘
```

---

## 三、模块分层设计

### 3.1 核心层 (core/)

| 模块 | 职责 | 接口定义 |
|------|------|----------|
| `kernel/` | Agent 执行内核，状态机管理 | `AgentKernel`, `StateMachine`, `Transition` |
| `loop/` | Ralph 循环实现，永不放弃 | `AgentLoop`, `LoopHooks`, `IterationResult` |
| `planner/` | 任务规划与分解 | `Planner`, `Task`, `Plan`, `PlanStrategy` |
| `executor/` | 工具执行引擎 | `Executor`, `ToolContext`, `ExecutionResult` |
| `reflector/` | 自我反思与改进 | `Reflector`, `Reflection`, `Improvement` |

### 3.2 端口层 (ports/)

| 端口 | 描述 | 核心方法 |
|------|------|----------|
| `memory/` | 记忆系统抽象 | `store()`, `retrieve()`, `consolidate()` |
| `tools/` | 工具系统抽象 | `register()`, `execute()`, `list_available()` |
| `model/` | LLM 模型抽象 | `chat()`, `embed()`, `batch_chat()` |
| `skills/` | Skills 系统抽象 | `install()`, `activate()`, `execute()` |
| `planner/` | 规划策略抽象 | `plan()`, `replan()`, `evaluate()` |
| `eval/` | 评测抽象 | `evaluate()`, `benchmark()`, `compare()` |

### 3.3 适配器层 (adapters/)

| 适配器 | 实现 | 适配目标 |
|--------|------|----------|
| `memory/sqlite/` | OpenAkita 现有 SQLite | `MemoryPort` |
| `memory/chroma/` | ChromaDB 向量存储 | `MemoryPort` |
| `model/anthropic/` | Anthropic API | `ModelPort` |
| `model/openai/` | OpenAI API | `ModelPort` |
| `model/local/` | Ollama/LM Studio | `ModelPort` |
| `tools/openakita/` | OpenAkita 现有工具 | `ToolPort` |
| `tools/mcp/` | MCP Server | `ToolPort` |
| `skills/agentskills/` | Agent Skills 规范 | `SkillPort` |

---

## 四、核心接口定义

### 4.1 AgentKernel 接口

```python
class AgentKernel(ABC):
    """Agent 执行内核 - 六边形架构核心"""

    @abstractmethod
    async def run(self, task: Task, context: KernelContext) -> KernelResult:
        """执行任务的主入口"""
        pass

    @abstractmethod
    async def plan(self, goal: str, context: KernelContext) -> Plan:
        """任务规划"""
        pass

    @abstractmethod
    async def execute(self, step: PlanStep, context: KernelContext) -> ExecutionResult:
        """执行单个步骤"""
        pass

    @abstractmethod
    async def reflect(self, result: ExecutionResult, context: KernelContext) -> Reflection:
        """反思执行结果"""
        pass

    @abstractmethod
    def get_state(self) -> AgentState:
        """获取当前状态"""
        pass

    @abstractmethod
    async def transition(self, event: Event) -> StateTransition:
        """状态转换"""
        pass
```

### 4.2 MemoryPort 接口

```python
class MemoryPort(ABC):
    """记忆系统端口"""

    @abstractmethod
    async def store(self, memory: Memory, context: StoreContext) -> MemoryId:
        """存储记忆"""
        pass

    @abstractmethod
    async def retrieve(self, query: MemoryQuery, context: RetrieveContext) -> list[Memory]:
        """检索记忆"""
        pass

    @abstractmethod
    async def consolidate(self, context: ConsolidationContext) -> ConsolidationResult:
        """记忆整合"""
        pass

    @abstractmethod
    async def forget(self, memory_id: MemoryId, context: ForgetContext) -> bool:
        """遗忘记忆"""
        pass
```

### 4.3 ToolPort 接口

```python
class ToolPort(ABC):
    """工具系统端口"""

    @abstractmethod
    async def execute(self, tool_call: ToolCall, context: ToolContext) -> ToolResult:
        """执行工具调用"""
        pass

    @abstractmethod
    async def batch_execute(
        self, tool_calls: list[ToolCall], context: ToolContext
    ) -> list[ToolResult]:
        """批量执行工具"""
        pass

    @abstractmethod
    def list_available(self, context: ListContext) -> list[Tool]:
        """列出可用工具"""
        pass

    @abstractmethod
    async def validate(self, tool_call: ToolCall) -> ValidationResult:
        """验证工具调用"""
        pass
```

---

## 五、融合策略

### 5.1 渐进式迁移路径

```
Phase 1: 骨架建设 (Week 1-2)
├── 创建 ports/ 目录和核心接口
├── 实现 OpenAkita 现有功能的适配器
├── 保持向后兼容，不改变现有 API
└── 验证: 运行现有测试套件

Phase 2: 内核抽象 (Week 3-4)
├── 重构 Agent 类，引入 AgentKernel
├── 提取 RalphLoop 为可插拔组件
├── 实现状态机抽象
└── 验证: 新旧 Agent 行为一致

Phase 3: 记忆系统重构 (Week 5-6)
├── 实现 MemoryPort 接口
├── 迁移 MemoryManager 到适配器模式
├── 支持多后端并行
└── 验证: 记忆功能无退化

Phase 4: 工具系统重构 (Week 7-8)
├── 实现 ToolPort 接口
├── 迁移 ToolCatalog 到新架构
├── 支持 MCP 适配器
└── 验证: 工具调用成功率

Phase 5: 模型网关重构 (Week 9-10)
├── 实现 ModelPort 接口
├── 抽象 LLMAdapter
├── 支持多 Provider 路由
└── 验证: 多模型切换正常

Phase 6: 多 Agent 协作 (Week 11-12)
├── 完善 AgentOrchestrator
├── 实现协作协议抽象
├── 支持跨实例通信
└── 验证: 多 Agent 协作流程

Phase 7: 上线准备 (Week 13-14)
├── 特性开关全覆盖
├── 灰度发布管线
├── 监控和告警
└── 验证: 线上环境稳定
```

### 5.2 特性开关设计

```python
class FeatureFlags:
    """特性开关配置"""

    # 内核开关
    KERNEL_V2 = "openakita.kernel.v2"  # 使用新内核
    RALPH_LOOP_V2 = "openakita.loop.v2"  # 新循环引擎

    # 记忆开关
    MEMORY_V2 = "openakita.memory.v2"  # 新记忆系统
    MEMORY_CHROMA = "openakita.memory.chroma"  # ChromaDB 后端

    # 工具开关
    TOOL_V2 = "openakita.tools.v2"  # 新工具系统
    TOOL_MCP_NATIVE = "openakita.tools.mcp_native"  # 原生 MCP

    # 模型开关
    MODEL_ADAPTER_V2 = "openakita.model.adapter.v2"  # 新适配器
    MODEL_STREAMING = "openakita.model.streaming"  # 流式输出

    @classmethod
    def is_enabled(cls, flag: str, default: bool = False) -> bool:
        """检查开关状态"""
        return os.environ.get(f"AKITA_FLAG_{flag.upper()}", str(default).lower()) == "true"
```

---

## 六、关键技术决策

### 6.1 状态管理

- **Checkpoint 策略**: 每次状态转换后自动持久化
- **Undo/Redo**: 基于 Command 模式实现
- **Crash Recovery**: 重启后从最近 checkpoint 恢复

### 6.2 并发模型

- **Task-Local Storage**: 使用 contextvars 隔离并发会话
- **工具并发**: 读-only 工具可并行，破坏性工具串行
- **Actor 模型**: 多 Agent 通信基于消息传递

### 6.3 可观测性

- **OpenTelemetry**: 全链路追踪
- **Metrics**: 关键指标采集
- **Logging**: 结构化日志，关联 Trace ID

---

## 七、向后兼容策略

### 7.1 API 兼容层

```python
# 旧 API 适配器
class LegacyAgentAdapter(AgentPort):
    """保持旧版 Agent 类接口"""

    def __init__(self, kernel: AgentKernel):
        self._kernel = kernel

    async def chat(self, message: str, context: LegacyContext) -> LegacyResponse:
        # 转换为新格式
        task = Task(description=message)
        result = await self._kernel.run(task, KernelContext())
        return LegacyResponse(content=result.content)
```

### 7.2 配置兼容

- `.env` 配置自动映射到新架构
- 旧配置文件平滑迁移
- 废弃配置警告机制

---

## 八、测试策略

### 8.1 测试金字塔

```
        ┌─────────────────┐
        │   E2E Tests     │  ← 关键用户旅程
        ├─────────────────┤
        │  Integration    │  ← 适配器测试
        │    Tests        │
        ├─────────────────┤
        │   Contract      │  ← 接口契约测试
        │    Tests        │
        ├─────────────────┤
        │   Unit Tests    │  ← 内核逻辑 (>80%)
        └─────────────────┘
```

### 8.2 契约测试

```python
@pytest.fixture
def memory_contract():
    """记忆端口契约测试"""
    return ContractTest(
        port=MemoryPort,
        cases=[
            ContractCase("store_retrieve", store_and_retrieve),
            ContractCase("consolidate", consolidate_memories),
            ContractCase("forget", forget_memory),
        ]
    )
```

---

## 九、文档与知识管理

### 9.1 架构决策记录 (ADR)

| ID | 决策 | 状态 |
|----|------|------|
| ADR-001 | 采用六边形架构 | 提议中 |
| ADR-002 | 使用 contextvars 隔离并发 | 提议中 |
| ADR-003 | 记忆系统多后端策略 | 提议中 |
| ADR-004 | 工具系统 MCP 集成 | 提议中 |
| ADR-005 | 特性开关实现方案 | 提议中 |

### 9.2 迁移指南

每个 Phase 完成后提供:
- 迁移检查清单
- 常见问题 FAQ
- 回滚步骤

---

## 十、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 架构过于复杂 | 开发效率降低 | 渐进式迁移，保持简单 |
| 性能退化 | 用户体验下降 | 持续性能测试，回归基准 |
| 破坏兼容性 | 现有用户流失 | 充分向后兼容，充分测试 |
| 迁移周期长 | 维护成本增加 | 并行开发，特性开关控制 |

---

## 十一、附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| Port (端口) | 六边形架构中的抽象接口层 |
| Adapter (适配器) | 端口的具体实现 |
| Kernel (内核) | Agent 执行的核心逻辑 |
| SPI | Service Provider Interface，服务提供者接口 |

### B. 参考资料

- [六边形架构 (Hexagonal Architecture)](https://alistair.cockburn.us/hexagonal-architecture/)
- [Anthropic Agent Patterns](https://www.anthropic.com/research/building-effective-agents)
- [OpenAkita Ralph Loop](src/openakita/core/ralph.py)
