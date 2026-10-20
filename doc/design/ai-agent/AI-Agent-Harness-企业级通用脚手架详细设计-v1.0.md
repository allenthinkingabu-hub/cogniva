# AI Agent Harness 企业级通用脚手架详细设计 v1.0

| 属性 | 内容 |
|---|---|
| 文档状态 | 2026-10-19；企业级 Agent 运行时与工程脚手架架构规范；指导 M03 及后续工程落地 |
| 适用系统 | Cogniva 平台（Cognition + Nova）多 Agent 协作系统及通用 Agentic 工程 |
| 直接上位架构 | [通用Agent-Harness参考架构与工程规范 v1.0](../../architecture/通用Agent-Harness-参考架构与工程规范-v1.0.md) |
| 相关详细设计 | [学生持续学习-AI-Agent群详细设计 v1.0](../学生持续学习-AI-Agent群详细设计-v1.0.md)、[LA-01 需求与C4详细设计 v1.0](../agents/LA-01-学习协调Agent-需求与C4详细设计-v1.0.md) |
| 核心目标 | 构建高可用、强隔离、具故障自愈与审计能力的企业级 Agent Harness 脚手架，彻底跨越玩具级 Demo 与工业生产系统的鸿沟 |

---

## 1. 架构定位：LangGraph 与 Harness 宿主的权责边界

在构建企业级 AI Agent 系统时，必须明确区分 **“图执行引擎”** 与 **“企业级受控宿主（Harness）”** 的本质差异。

```
                    ┌────────────────────────────────────────────────────────┐
                    │               Harness Host Control Ring                │
                    │                                                        │
                    │   ┌───────────────┐               ┌────────────────┐   │
   [Inbound Event] ───> │  on_run_load  │ ──(advance)─> │ before_context │ ──┼──> [Protected Context]
                    │   └───────────────┘               └────────────────┘   │
                    │                                           │            │
                    │   ┌───────────────┐               ┌────────────────┐   │
                    │   │  after_model  │ <──(audit)─── │  before_model  │ <─┼──> [Model Boundary]
                    │   └───────────────┘               └────────────────┘   │  (Budget / Dest check)
                    │           │                                            │
                    │   ┌───────────────┐               ┌────────────────┐   │
                    │   │ before_action │ ──(gate)────> │  after_action  │ ──┼──> [Tool / Sub-Agent]
                    │   └───────────────┘               └────────────────┘   │  (Idempotent operation_ref)
                    │           │                                            │
                    │   ┌───────────────┐               ┌────────────────┐   │
                    │   │before_chkpnt  │ ──(CAS fence)─│before_finalize │ ──┼──> [Outcome / Receipt]
                    │   └───────────────┘               └────────────────┘   │
                    └────────────────────────────────────────────────────────┘
                                     │ (drives & wraps)
                                     ▼
                    ┌────────────────────────────────────────────────────────┐
                    │            LangGraph / StateGraph Engine               │
                    │    [Node: Router] ──> [Node: Explainer] ──> [State]    │
                    └────────────────────────────────────────────────────────┘
```

### 1.1 开源框架（LangChain / LangGraph / Deep Agent）的定位
- **开源框架的角色**：是算法与执行的**“有向图引擎与局部调度器”**（StateGraph、Node/Edge 拓扑、条件分支、短时检查点）。
- **Happy-Path 致命假设**：开源库默认假设网络不中断、Worker 不会宕机（Crash）、外部大模型不超时、模型可以自由决定调用何种工具（模型自授权）。
- **商业化分工局限**：开源社区将多租户隔离、密钥保密、分布式租约与审计放到闭源云端（如 LangSmith / LangGraph Cloud），但依然无法解决企业私有数据主权、跨语言（Java 与 Python）事务协同以及本地离线测试问题。

### 1.2 Harness（企业级宿主）的核心职责
- **Harness 的角色**：是外层的**“安全控制环与分布式受控运行时（Control Ring & Host）”**。
- **不可逾越的原则**：
  1. **大模型绝对不可信**：模型输出的不是“命令（Command）”，而仅仅是“候选提案（Candidate Proposal）”；
  2. **权限由宿主裁决**：只有宿主代码在不可绕过的 `before_action` 闸门校验当前身份、配额与版本后，才能构造合法的受控动作；
  3. **分布式可靠性**：通过租约（Lease）、CAS 乐观锁防脑裂（Fencing Token）、消息去重（Inbox）与事务外发（Outbox），确保系统在任何节点宕机时可自愈恢复，不丢失状态，不产生重复业务副作用。

---

## 2. 脚手架功能性需求清单（Scaffold Functional Requirements - S-FR）

基于通用规范第 1.3 节（H-FR-01 ～ H-FR-14），脚手架必须原生内建以下 **12 项企业级功能特性**：

| 需求编号 | 功能特性名称 | 核心行为与验收规范 | 追溯规范 |
|---|---|---|---|
| **S-FR-01** | **不可绕过的 9 阶段生命周期 Hooks** | 提供核心驱动循环 `advance(run, fencing_token)`，严格依次触发 9 大拦截点：`on_run_load` → `before_context` → `before_model` → `after_model` → `before_action` → `after_action` → `before_checkpoint` → `before_finalize` → `after_finalize`。禁止中间件穿透或越过 Hook 直接调用工具。 | H-FR-01, H-FR-02 |
| **S-FR-02** | **六边形架构与纯净领域层** | 业务 Agent（LA-01～LA-05）位于纯净 Domain 层，零第三方技术库依赖（不导入数据库驱动、HTTP 客户端或厂商 SDK）；所有外围交互抽象为严格的 Ports（`ModelPort`, `PolicyPort`, `BudgetPort`, `CheckpointPort`, `EvidencePort`）。 | 规范 4.1 节 |
| **S-FR-03** | **进程级物理隔离与密钥代理** | 架构拆分为独立双进程：Worker 进程处理 Agent 业务图但**不持任何 API 密钥**；Provider 独立进程管理 Key、速率限制与出网审计。脚手架默认提供 100% 确定性的 `FakeProvider` 实现本地离线闭环。 | H-FR-04, H-FR-14 |
| **S-FR-04** | **分布式租约与单调 CAS Fencing** | 采用数据库持久租约（Lease）控制并发执行权；每次推进持久化状态必须验证单调递增的 `fencing_token`。旧 Worker 僵死复活后的写操作必须被数据库 CAS 阻断，杜绝脑裂（Split-brain）。 | H-FR-06, 规范 8.3 节 |
| **S-FR-05** | **操作幂等键与未知对账机制** | 工具执行与业务提交前必须先持久化全局唯一业务操作键（`operation_ref`）；遭遇网络超时时，状态标记为 `unknown`，由专职对账器（Reconciler）执行指数退避查询，严禁盲目自动重试非幂等写操作。 | H-FR-05, 规范 8.7 节 |
| **S-FR-06** | **长上下文保护项与 ContextManifest** | 上下文装配实行优先级保护：系统指令、学生当前否定句（如“周末不学习”）、当前核心目标为最高优先级保护片段；显式输出 `ContextManifest`，记录每个片段的来源、哈希、版本、Token 预留与截断理由。 | H-FR-03, 规范 8.4 节 |
| **S-FR-07** | **分层记忆治理与墓碑删除** | 内存与存储明确分层：权威业务事实（Java）、当前 Run 派生工作记忆、会话摘要、可推断长期记忆；支持依据学生注销/合规要求的墓碑删除（Tombstone），阻止已删除信息被 Checkpoint 重新复活。 | H-FR-03, 规范 8.5 节 |
| **S-FR-08** | **原子父子预算预占与守恒** | 提供 `BudgetPort`，实现模型 Token 与费用的原子预占（Reserve）、分配（Allocate）、结算（Settle）与释放；多 Agent 委派时子预算从父预算原子切分，严格保证 `子预算分配 + 父已花费 <= 批准总额`。 | H-FR-04, H-FR-08 |
| **S-FR-09** | **死循环与无进展熔断（Loop Breaker）** | 终止条件由多重维度判定：步数上限、绝对截止时间（Deadline）、预算耗尽、用户主动取消；内建“无进展检测”——基于输入/动作/参数哈希连续 3 次无新状态变化时强制熔断退出。 | H-FR-02, 规范 8.1 节 |
| **S-FR-10** | **树状受控多 Agent 协同协议** | 严禁网状自由群聊，确立 LA-01（Coordinator）为根，LA-02～05 为叶角色的固定拓扑；标准化 `Handoff` 委派契约与 `ChildResult` 状态聚合，明确区分 `completed`、`partial`、`needs_input`（汇聚澄清问题）。 | H-FR-08, 规范 8.9 节 |
| **S-FR-11** | **双向 Stub 离线联调生态** | 脚手架内置完整的双向 Stub：JavaStub 供 Python 离线模拟业务上下文查询与收据发放；AgentStub 供 Java 离线模拟 Agent 异步响应，使双端在脱离对端服务时依然可独立跑通全链路。 | Master Plan I-03 |
| **S-FR-12** | **消费者驱动的契约校验与 DTO 生成** | 提供自动化工具链，读取 `contracts/` 下的 OpenAPI 与 JSON Schema，一键生成 Pydantic v2 强类型 DTO，并执行漂移检测（Drift Detection）。 | Master Plan M03 |

---

## 3. 脚手架非功能性需求清单（Scaffold Non-Functional Requirements - S-NFR）

| 需求编号 | 非功能分类 | 验收指标与强制性约束 | 对应质量目标 |
|---|---|---|---|
| **S-NFR-01** | **安全性（Security & Zero-Trust）** | 1. **零密钥泄露**：Worker 进程与运行时环境绝不持有任何大模型 API Key；<br>2. **零越权执行**：所有受控动作强制通过 `before_action` 代码拦截，模型生成的伪指令无法跳过权限核验；<br>3. **敏感数据脱敏**：日志、Trace 和异常中严禁打印学生隐私数据（PII）、Cookie 与 Token。 | 规范 10.2 节 |
| **S-NFR-02** | **高可靠与故障自愈（Reliability & Crash Recovery）**| 1. **消息重投幂等**：同一消息重复投递 10 次，业务逻辑与副作用有且仅执行一次；<br>2. **无缝崩溃恢复**：Worker 进程在任意 Step 强行退出（SIGKILL）后，重启能从上一 Checkpoint 自动恢复并重新调度；<br>3. **租约脑裂防护**：旧 Worker 续租失败或 GC 假死后，写操作 100% 被数据库 CAS 阻断。 | 规范 10.3 节 |
| **S-NFR-03** | **确定性与可测试性（Determinism & Testability）** | 1. **本地 100% 确定性**：依赖 FakeProvider 与 Synthetic Data，单测套件在任何断网克隆机上均能稳定全绿；<br>2. **极致极速单测**：Domain 与 Rules 纯逻辑单元测试执行时间小于 5 秒；<br>3. **故障注入就绪**：原生支持网络超时、并发写冲突、预算耗尽、租约过期等故障注入用例。 | 规范 10.1 节 |
| **S-NFR-04** | **性能与并发边界（Performance & Concurrency）** | 1. **全异步非阻塞**：FastAPI + asyncpg + HTTPX 全异步链路，禁止同步阻塞操作占用事件循环；<br>2. **并发硬上限**：限制单个 Run 的子 Agent 并发深度（默认 max_depth <= 2）与工具并发数，防止协程爆炸。 | 规范 10.4 节 |
| **S-NFR-05** | **可观测性与合规审计（Observability & Audit）** | 1. **标准 OpenTelemetry 语义**：规范生成 trace/run/step/operation 关联链路；<br>2. **审计日志不可采样**：高风险变更与业务提交的审计记录 100% 落盘，严禁采样丢弃；<br>3. **低基数指标**：Prometheus 标签杜绝包含 student_id 或动态参数。 | 规范 8.11, 10.5 节 |
| **S-NFR-06** | **架构纯粹性与可替换性（Architectural Purity）** | 1. **框架无侵入**：LangGraph 或其他开源框架仅作为 Adapter 插件，更换底层图框架不影响领域层代码；<br>2. **类型安全**：100% 具备 Python 类型提示（Type Hints），通过 Mypy 严格检查。 | 规范 10.6 节 |

---

## 4. 服务命名与工程目录结构落地

根据微服务与云原生规范，项目杜绝直接使用宽泛的 `services/python/` 命名，而是统一按照**能力域（Domain Capability）**命名。

### 4.1 顶级微服务命名
- **`services/cogniva-learning-agent/`**：核心 Agent Harness 运行时微服务（Python），负责 LA-01 协同调度、叶 Agent 执行、LangGraph 编排与状态流转；
- **`services/cogniva-model-provider/`**：独立大模型网关微服务（Python），专职持有 Key、厂商 SDK 出网边界、Token 计数预测与用量审计；
- **`services/cogniva-learning-core/`**：[B线] Java 核心业务应用；
- **`services/cogniva-knowledge-service/`**：[B线] Java 题库与知识母本微服务。

### 4.2 `cogniva-learning-agent` 内部工程布局

```text
services/cogniva-learning-agent/
├── pyproject.toml                         # 模块依赖与工具锁配置 (uv / pip)
├── Dockerfile                             # 生产无特权容器镜像
├── migrations/                            # Alembic 执行库迁移脚本
│   ├── env.py
│   └── versions/
│       └── 001_agent_runtime.py           # runs, steps, checkpoints, leases, inbox, outbox
├── src/
│   └── cogniva_agent/
│       ├── domain/                        # 【纯净领域层】零外部依赖
│       │   ├── models/                    # Run, Step, Event, Session, IntentProposal
│       │   ├── coordination/              # CoordinationPlan, WorkflowCatalog, TaskHandoff
│       │   └── rules/                     # LA-01 纯规则意图识别器, 循环终止判定
│       │
│       ├── ports/                         # 【六边形端口层】抽象接口规范
│       │   ├── model_port.py              # 大模型调用与候选提案接口
│       │   ├── policy_port.py             # 授权与安全检查接口
│       │   ├── budget_port.py             # 预算原子预占与结算接口
│       │   ├── checkpoint_port.py         # 状态检查点接口
│       │   ├── receipt_port.py            # Java 业务收据与事实查询接口
│       │   └── evidence_port.py           # 证据检索与 RAG 接口
│       │
│       ├── harness/                       # 【Harness 内核】外层安全控制环
│       │   ├── kernel.py                  # advance() 驱动循环, 状态机 CAS
│       │   ├── hooks.py                   # 9 阶段生命周期拦截器注册与分发
│       │   ├── lease.py                   # 分布式租约与单调 fencing_token 校验
│       │   ├── context.py                 # ContextManifest, 长上下文保护项装配
│       │   └── reconciler.py              # 未知状态操作对账器
│       │
│       ├── agents/                        # 【Agent 群实现】
│       │   ├── la01_coordinator.py        # LA-01 学习协调 Agent
│       │   ├── la02_diagnostic.py         # LA-02 归因分析 Agent
│       │   ├── la03_explainer.py          # LA-03 概念讲解 Agent
│       │   ├── la04_planner.py            # LA-04 路径规划 Agent
│       │   └── la05_personal_advisor.py   # LA-05 个人建议 Agent
│       │
│       ├── workflows/                     # 【LangGraph 编排层】确定性图定义
│       │   ├── state.py                   # AgentState 定义
│       │   ├── explain_flow.py            # 讲解协同模板图
│       │   ├── practice_flow.py           # 练习协同模板图
│       │   └── replan_flow.py             # 重规划协同模板图
│       │
│       └── adapters/                      # 【适配器层】技术实现
│           ├── api/                       # FastAPI 内部接收与健康检查接口
│           ├── persistence/               # SQLAlchemy 2 异步 Core + Checkpointer 适配
│           ├── messaging/                 # RabbitMQ / aio-pika Inbox/Outbox 消费与发布
│           ├── provider_client/           # 与 cogniva-model-provider 通信的客户端
│           └── stubs/                     # 供本地开发的 JavaStub 与 FakeClient
│
└── tests/
    ├── conftest.py                        # 全局 fixtures 与 Fake 环境注入
    ├── unit/                              # 领域实体、纯规则意图识别、DTO 校验 (毫秒级)
    ├── contract/                          # JSON Schema 契约校验与边界负例测试
    └── harness/                           # 9阶段 Hook 拦截、CAS fence 冲突、超时对账、重投10次测试
```

### 4.3 `cogniva-model-provider` 内部工程布局

```text
services/cogniva-model-provider/
├── pyproject.toml                         # Provider 模块依赖配置
├── Dockerfile
├── src/
│   └── cogniva_provider/
│       ├── domain/                        # ModelProfile, 价格表版本, 计数器
│       ├── ports/                         # 统一供应商接口
│       ├── adapters/
│       │   ├── fake_provider.py           # 确定性 Fake 实现 (根据 Schema 动态生成合法结构化返回)
│       │   ├── openai_adapter.py          # OpenAI 官方 SDK 适配
│       │   └── qwen_adapter.py            # 通义千问/DashScope 适配
│       └── server/                        # Provider HTTP/gRPC 出网代理服务
└── tests/
    ├── test_fake_provider.py
    └── test_token_accounting.py
```

---

## 5. 技术依赖选型矩阵（Python 维护线）

| 技术组件 | 选定方案 | 选型依据与职责 |
|---|---|---|
| **编程语言与包管理** | Python 3.11+ / uv | 官方支持维护线，严格工程结构与依赖锁管理 |
| **类型系统与 DTO** | Pydantic v2 | 严格 Schema 运行时反序列化校验与性能加速 |
| **API 服务框架** | FastAPI + Uvicorn | 异步高性能 HTTP 接入与 ASGI 接口 |
| **Agent 状态图** | LangGraph 0.2+ | 有向图节点控制与检查点流转（置于 Adapter 层） |
| **数据访问与迁移** | SQLAlchemy 2.0+ (asyncpg) + Alembic | 全异步 PostgreSQL 交互，支持 CAS 与复合租户键 |
| **异步消息驱动** | aio-pika / async AMQP | 支持 Publisher Confirm 与持久化消费确认 |
| **可观测与日志** | structlog + OpenTelemetry SDK | 结构化 JSON 字段绑定，全链路 Trace 上下文传递 |
| **测试套件** | pytest + pytest-asyncio + pytest-mock | 异步与同步测试兼备，支持轻量级故障注入 |

---

## 6. 实施演进路线（从 M03 到后续任务）

1. **Step 1 (当前目标 M03)**：
   - 建立 `services/cogniva-learning-agent` 与 `services/cogniva-model-provider` 双工程骨架；
   - 落地 `pyproject.toml` 依赖锁定与 src 模块结构；
   - 引入核心 Domain 模型、Ports 抽象与 `FakeProvider`；
   - 验证服务能空载健康启动并通过纯离线单元测试。
2. **Step 2 (对接 A-01/M06 迁移)**：
   - 完成 Alembic 真实数据库表迁移（runs, steps, checkpoints, leases）。
3. **Step 3 (对接 A-02/M12 运行时)**：
   - 将 LangGraph 状态图完整挂载到 Harness 9 阶段 Hook 控制内核。
