# 企业级 AI Agent 架构知识体系全景指南 (v1.0)

| 属性 | 内容 |
|---|---|
| 文档状态 | 2026-10-25；v1.0 基线版本；指导企业级通用 AI Agent 架构设计与技术选型 |
| 体系定位 | 面向高可用、金融级/工业生产级系统，系统性阐述 AI Agent 完整技术栈与认知边界 |
| 核心哲学 | **“不把概率模型直接接入业务系统；图引擎负责思考与路由，Harness 宿主负责事务与安全”** |
| 配套工程实现 | [AI-Agent-端到端完全落地详细设计与工程实现指南-v1.0.md](./03-AI-Agent-端到端完全落地详细设计与工程实现指南-v1.0.md) |

---

## 目录
- [一、 AI Agent 架构七层全景总览](#一-ai-agent-架构七层全景总览)
- [二、 逐层核心原理与技术栈深度解构](#二-逐层核心原理与技术栈深度解构)
  - [L1. 基础设施与大模型服务网关 (LLMOps Gateway)](#l1-基础设施与大模型服务网关-llmops-gateway)
  - [L2. 受控宿主运行时层 (Harness & Control Ring Kernel)](#l2-受控宿主运行时层-harness--control-ring-kernel)
  - [L3. 认知范式与编排架构层 (Cognition & Orchestration)](#l3-认知范式与编排架构层-cognition--orchestration)
  - [L4. 记忆层级与状态持久化 (Memory Hierarchy & State)](#l4-记忆层级与状态持久化-memory-hierarchy--state)
  - [L5. 知识增强与工具生态层 (RAG & Tool/Environment)](#l5-知识增强与工具生态层-rag--toolenvironment)
  - [L6. 零信任安全与合规治理层 (Guardrails & Governance)](#l6-零信任安全与合规治理层-guardrails--governance)
  - [L7. 可观测性与持续评测运维层 (Observability & EvalOps)](#l7-可观测性与持续评测运维层-observability--evalops)
- [三、 生产级典型反模式 (Anti-Patterns)](#三-生产级典型反模式-anti-patterns)
- [四、 架构演进与技术选型决策矩阵 (Decision Matrix)](#四-架构演进与技术选型决策矩阵-decision-matrix)

---

## 一、 AI Agent 架构七层全景总览

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                  Layer 7: 可观测性与持续评测运维层 (Observability & EvalOps)      │
│     [OpenTelemetry Tracing]   [LLM-as-a-Judge 自动化评测]   [影子流量/回归基准]    │
└──────────────────────────────────────────────────────────────────────────────┘
                                       ▲
┌──────────────────────────────────────────────────────────────────────────────┐
│                  Layer 6: 零信任安全与合规治理层 (Guardrails & Governance)       │
│     [间接注入防御]   [输出结构校验 Schema Gate]   [PII 脱敏与不可篡改审计收据]      │
└──────────────────────────────────────────────────────────────────────────────┘
                                       ▲
┌──────────────────────────────────────────────────────────────────────────────┐
│                  Layer 5: 知识增强与工具生态层 (RAG & Tool Environment)         │
│     [四层知识库(母本与投影)]   [Hybrid RAG(BM25+向量)]   [MCP协议 / 代码沙箱]    │
└──────────────────────────────────────────────────────────────────────────────┘
                                       ▲
┌──────────────────────────────────────────────────────────────────────────────┐
│                  Layer 4: 记忆层级与状态持久化 (Memory Hierarchy & State)        │
│     [短期情境 Context Window]   [工作记忆 Scratchpad]   [持久语义向量/图谱记忆]    │
└──────────────────────────────────────────────────────────────────────────────┘
                                       ▲
┌──────────────────────────────────────────────────────────────────────────────┐
│                  Layer 3: 认知范式与编排架构 (Cognition & Orchestration)        │
│     [ReAct / Plan-and-Solve]   [多Agent协作(主从分流)]   [LangGraph 拓扑图]     │
└──────────────────────────────────────────────────────────────────────────────┘
                                       ▲ (Driven & Wrapped by)
┌──────────────────────────────────────────────────────────────────────────────┐
│                  Layer 2: 受控宿主运行时层 (Harness & Control Ring Kernel)      │
│     ★ 9 阶段生命周期钩子  ★ Fencing Token (CAS防脑裂)  ★ 算力原子预算预占      │
│     ★ 工具副作用拦截/幂等 operation_ref                ★ 确定性业务状态机       │
└──────────────────────────────────────────────────────────────────────────────┘
                                       ▲
┌──────────────────────────────────────────────────────────────────────────────┐
│                  Layer 1: 基础设施与大模型服务网关 (LLMOps Gateway)             │
│     [多模型路由/负载均衡]   [流式背压控制]   [语义缓存 (Semantic Cache)]  [算力配额] │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、 逐层核心原理与技术栈深度解构

### L1. 基础设施与大模型服务网关 (LLMOps Gateway)
* **定位**：Agent 应用层与异构底层算力（大模型供应方）之间的抽象隔离层。
* **核心能力**：
  1. **多供应商与私有化统一适配**：屏蔽 OpenAI、Anthropic、DeepSeek、DashScope 或本地 vLLM/Ollama 的请求/响应差异，提供统一抽象 API；
  2. **智能路由与优雅降级（Fallback）**：基于响应延迟（Latency）、算力费用（Cost）、限流状态（HTTP 429 Rate Limit）自动调度主备模型（如主模型超时时平滑切换备用轻量模型）；
  3. **语义缓存（Semantic Cache）**：利用稠密嵌入向量对高频只读请求建立缓存（相似度 $\ge 0.95$ 直接返回），大幅降低延迟与 Token 开销（注意：含个人上下文的私有请求禁止跨租户复用）；
  4. **流式传输与背压控制（Backpressure）**：全异步 Server-Sent Events (SSE) / WebSocket 传输，保证网络抖动时支持客户端断线重连与流式中断。

---

### L2. 受控宿主运行时层 (Harness & Control Ring Kernel)
* **定位**：**Agent 的“操作系统内核（Kernel）”**。负责约束、托管和安全驱动上层的无状态推理图。
* **核心防线**：
  1. **不可绕过的 9 阶段执行控制环（9 Lifecycle Hooks）**：
     * `on_run_load`：验证租户身份、时效租约（Lease）与软删除墓碑（Tombstone）；
     * `before_context`：依据用户授权目的（Purpose）对敏感数据切片执行合规脱敏与过滤；
     * `before_model`：预测 Token 用量，出网域名白名单核验，**原子预占模型算力预算**；
     * `after_model`：Pydantic Schema 强类型反序列化校验，剥离模型非法生成的提权标识；
     * `before_action`：**核心安全门禁**，由宿主严格基于用户身份构造 `AuthorizedToolCall`，模型自行填写的 `permit=true` 直接被代码阻断；
     * `after_action`：强制绑定全局唯一不可变操作键（`operation_ref`），遭遇网络未知超时先标 `unknown` 并转入对账流程，严禁盲目重试非幂等操作；
     * `before_checkpoint`：单调递增 `fencing_token` + 数据库 CAS 乐观锁持久化状态，杜绝分布式脑裂与覆盖写；
     * `before_finalize`：汇总已完成与未完成目标，生成只读全局 Run Receipt（审计收据）；
     * `after_finalize`：基于 Outbox 模式异步发布终态事件与不可篡改审计日志。
  2. **确定性业务优先原则**：
     * 涉及金钱计算、客观评分、用户鉴权与状态机跃迁，必须由确定性代码执行，坚决不委托给概率论大模型。

---

### L3. 认知范式与编排架构层 (Cognition & Orchestration)
* **定位**：Agent 的推理思考与任务规划大脑（大脑决策）。
* **四大认知模式（Reasoning Patterns）**：
  * **CoT (Chain-of-Thought)**：在输出最终答案前，强制展开思维链步骤；
  * **ReAct (Reason + Act)**：Thought（思考） $\to$ Action（选择工具） $\to$ Observation（观察结果）的三元组循环推进；
  * **Plan-and-Solve**：宏观规划器先生成完整子任务 DAG，再由执行器拓扑遍历，遇到阻碍触发动态 Replanning；
  * **Reflection / Self-Correction**：引入 Critic 机制，对生成的草稿按照评分量表执行自我批判与打分修正。
* **多 Agent 协作拓扑（Multi-Agent Patterns）**：
  * **Orchestrator-Workers（主从路由树）**：协调 Agent 作为根节点负责分流与最终结果聚合，专业叶子 Agent（如讲解、出题、排程）互不越权；
  * **Hierarchical State Graph（分层受控状态图）**：利用 LangGraph 显式定义状态节点流转规则，最大子图递归深度严格 $\le 2$，禁止网状任意扩散；
  * **Human-in-the-Loop（人机协同断点）**：关键高危操作进入 `waiting_user` 挂起状态，通过 Webhook/消息队列等待人工审核恢复。

---

### L4. 记忆层级与状态持久化 (Memory Hierarchy & State)
* **定位**：解决大模型无状态特性的“时间与经验连续性系统”。
* **三层记忆金字塔**：
  1. **短期工作记忆（Working Memory）**：
     * 当前运行窗口上下文（Context Window）与临时推理演算便签（Scratchpad）；
     * 采用 ContextManifest 管理优先级，超出上限时执行确定性滑动窗口与语义上下文压缩（Summarization）；
  2. **情境会话记忆（Episodic Memory / Session State）**：
     * 记录单次长周期任务的执行轨迹、工具调用入参回包、中间 Checkpoint 快照，支持节点崩溃后秒级断点续跑；
  3. **长期语义记忆（Long-term Semantic Memory）**：
     * 存储跨会话的用户画像、错题本、历史偏好与技能画像；
     * 基于向量库与图谱混合检索按需加载，按租户和用户 ID 物理分区隔离。

---

### L5. 知识增强与工具生态层 (RAG & Tool/Environment)
* **定位**：为 Agent 提供抗幻觉的外部事实（Grounding）与现实交互能力（Action）。
* **工业级四层知识库模型**：
  * **原始资料层**：经合法授权的原始文档快照、校验摘要与授权存证；
  * **领域母本层**：教研审核通过的实体节点、权威关系网络、审核真题与版本清单；
  * **个人知识层**：用户专属的笔记、错因归因与私人标注，默认私有隔离；
  * **检索投影层**：派生的 BM25 词项索引与 pgvector 向量索引，随时可基于母本重建。
* **高级 RAG 检索管线**：
  * 结构化精确查询 $\to$ Hybrid Search（中文精确分词 + 密集向量） $\to$ Cross-Encoder 重排（Rerank） $\to$ 证据充分性判定（Evidence Sufficiency Check） $\to$ 生成带确定溯源锚点的回答；
* **标准化工具交互（MCP & Sandbox）**：
  * 采用 **MCP（Model Context Protocol）** 开放协议解耦工具提供方；
  * 危险代码执行（Code Interpreter）置于无网络、限制 CPU/内存的 Docker/WASM 隔离沙箱中。

---

### L6. 零信任安全与合规治理层 (Guardrails & Governance)
* **定位**：构建纵深防御，保障系统免受恶意对抗攻击与数据泄露。
* **核心防线**：
  * **输入防注入（Input Guardrails）**：清洗直接越狱指令；对第三方抓取网页/文件标记为“不可信数据源”，阻断间接 Prompt 注入（Indirect Prompt Injection）；
  * **最小权限原则（PoLP）**：子任务仅授予其所需的最小工具白名单；
  * **输出安全过滤（Output Guardrails）**：通过 Pydantic/JSON Schema 拦截幻觉字段；敏感信息（PII）自动正则脱敏；
  * **合规与审计留痕**：每一次调用生成不可抵赖的执行收据，审计日志 100% 持久化存储。

---

### L7. 可观测性与持续评测运维层 (Observability & EvalOps)
* **定位**：击穿 Agent 黑盒，驱动模型与 Prompt 的持续质量演化。
* **可观测性标准（Observability）**：
  * 基于 **OpenTelemetry** 语义规范，追踪 `TraceId` $\to$ `RunId` $\to$ `StepId` $\to$ `ModelCallId` $\to$ `ToolCallId`；
  * 记录每个 Step 的 Token 消耗、网络耗时、中间状态快照与错误堆栈。
* **持续自动化评测管线（EvalOps）**：
  * **Golden Benchmark 基准集**：构建覆盖常态与极端边界场景的高质量测试集；
  * **双重自动化打分机制**：
    * 确定性规则校验（Schema 合法性、工具入参准确率、禁用词检查）；
    * LLM-as-a-Judge（基于 G-Eval 框架对准确度、忠实度、完整度进行多维度打分）；
  * **CI/CD 回归门禁**：代码与 Prompt 提测时自动触发全量离线评估，准确率下降或幻觉率超标直接阻断合入。

---

## 三、 生产级典型反模式 (Anti-Patterns)

| 常见反模式 | 致命后果 | 正确架构做法 |
| :--- | :--- | :--- |
| **1. 盲目追求完全自治 Agent** | Agent 陷入思考死循环，或擅自修改数据库造成重大资损。 | 业务写操作与关键状态转移由**确定性状态机**控制，高风险操作引入 Human-in-the-loop。 |
| **2. 混淆“图引擎”与“受控宿主”** | 将网络请求、数据库写入裸写在 LangGraph 节点内，节点崩溃时状态丢失或脏写。 | 图引擎仅作为无状态逻辑流，所有写入与外呼受控于 **Harness 的 9 阶段生命周期钩子**。 |
| **3. 向量库万能论 (Vector-Only RAG)** | 无法保证专业领域（如法律、金融、医学）的权威口径与时效性，出现看似通顺的伪事实。 | 建立**四层知识库模型**，结合结构化属性过滤、图谱关系与精准 BM25 混合检索。 |
| **4. 未知超时盲目重试 (Blind Retry)** | 第三方支付或核心外部 API 网络超时后重复调用，导致多次扣款或重复下单。 | 强制持久化 `operation_ref`，遇到网络超时先标 `unknown` 并挂起，由专职对账器异步对账。 |

---

## 四、 架构演进与技术选型决策矩阵 (Decision Matrix)

```
                            业务是否包含持久化写操作/数据删改？
                                           │
                           ┌───────────────┴───────────────┐
                           ▼ NO                            ▼ YES
                  是否需要调用外部工具？                  业务是否涉及金钱、隐私或高合规？
                           │                                       │
                ┌──────────┴──────────┐                 ┌──────────┴──────────┐
                ▼ NO                  ▼ YES             ▼ NO                  ▼ YES
         【轻量级 RAG】          【标准 ReAct】     【受控工作流】         【必须强依赖 Harness】
      向量检索 + 提示词工程    LangChain/CrewAI    LangGraph 状态图      Harness 宿主环 + CAS 锁
      关注：召回率与时延      关注：工具解析准确度  关注：节点分支路由   + 预算预占 + 幂等收据 + EvalOps
```
