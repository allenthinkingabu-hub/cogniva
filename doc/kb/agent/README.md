# AI Agent 架构知识库与落地规范指南索引 (Knowledge Base Index)

| 属性 | 内容 |
|---|---|
| 知识库维护域 | 企业级 AI Agent 架构体系、受控宿主（Harness）与端到端闭环落地工程 |
| 命名规则 | `[两位序号]-[领域前缀]-[主题名称]-[版本号].md` |
| 版本控制规则 | 遵循 Semantic Versioning (语义化版本)，每次架构重大变更升级主/次版本号，保持历史文档不可变溯源 |
| 状态与基线 | 2026-10-25 正式建立 v1.0 基线 |

---

## 目录与文件导航

```text
doc/kb/agent/
├── README.md                                                 # [当前索引] 知识库结构与版本指南
├── 01-AI-Agent-企业级架构知识体系全景指南-v1.0.md             # [L1-L7 全景理论 (中文版)] 顶层战略蓝图与技术选型决策
├── 01-AI-Agent-Enterprise-Architecture-Knowledge-System-Guide-v1.0.md # [L1-L7 Architecture (English Edition)] Global Panorama
├── 02-AI-Agent-Harness-受控宿主深度原理解析-v1.0.md           # [核心机理] 9阶段生命周期、CAS防脑裂与状态机
├── 03-AI-Agent-端到端完全落地详细设计与工程实现指南-v1.0.md   # [工程施工] 4大套件代码模型、DDL、自包含RAG与EvalOps
└── deep-dive/                                                # [分层专项深度解构系列 (Deep Dive Series)]
    ├── 01-AI-Agent-L1-LLMOps网关深度架构与实战全景.md         # [L1 中文深度篇] 异构适配、动态路由、语义缓存与流式背压
    ├── 01-AI-Agent-L1-LLMOps-Gateway-Architecture-Deep-Dive.md # [L1 English Deep Dive] Resilience, Backpressure & Latency
    ├── cases/                                                # [生产故障 RCA 实战案例库 (STAR+L 模型)]
    │   ├── 01-L1-Case-01-稳定性抖动与SLA容灾降级-RCA实战.md   # [Case 01] 首字延迟暴增/429爆发/对冲双发与200ms自愈
    │   ├── 01-L1-Case-02-长连接背压吞吐瓶颈与内存OOM-RCA实战.md # [Case 02] 慢客户端积压/Pod内存打满OOMKilled与内核背压
    │   └── 01-L1-Case-03-Token成本失控与语义缓存对账-RCA实战.md # [Case 03] 首月$18万天价账单/L1-L3防越权语义缓存/削减69%成本
    └── specs/                                                # [核心子系统工程研发规格说明书 (SRS 全家桶)]
        ├── 00-L1-LLMOps网关全局需求规格总说明书-v1.0.md          # [Master SRS] 全局定位/单进程流水线/5大公共通用需求与跨模块治理
        ├── 01-L1-Sys1-异构模型统一驱动与适配器-需求规格说明书-v1.0.md # [系统 1 SRS] 驱动SPI模式/规范化协议/思维链提取/0.5ms极速
        ├── 02-L1-Sys2-多维智能路由与断路降级引擎-需求规格说明书-v1.0.md # [系统 2 SRS] 滑动窗口指标/多维打分/1500ms对冲双发/200ms断路降级
        ├── 03-L1-Sys3-防越权向量语义缓存与控费引擎-需求规格说明书-v1.0.md # [系统 3 SRS] L1-L3三级缓存/租户ACL硬过滤/反语义漂移/Prompt对齐
        └── 04-L1-Sys4-流式背压与长连接治理引擎-需求规格说明书-v1.0.md # [系统 4 SRS] 内核Socket监听/HTTP2流控背压/Zero-OOM/主动取消
```

---

## 核心文档的定位与阅读指引

### 1. 全景蓝图篇
* **[01-AI-Agent-企业级架构知识体系全景指南-v1.0.md](./01-AI-Agent-企业级架构知识体系全景指南-v1.0.md)** / [English Edition](./01-AI-Agent-Enterprise-Architecture-Knowledge-System-Guide-v1.0.md)
* **核心回答**：**What & Why（是什么、为什么、业界全局技术选型是什么、认知边界在哪里）**；
* **适用受众**：系统架构师、技术评审委员会、高阶求职/晋升答辩、技术管理者；
* **核心内容**：L1~L7 架构分层大图、四大认知模式（ReAct/Plan-and-Solve/Reflection）、四层知识库模型、生产级 4 大典型反模式、架构演进决策矩阵。
* **语言版本**：提供中文完整版与面向跨国团队/顶会的专业英文版（100% 完整对应）。

### 2. 内核机理篇
* **[02-AI-Agent-Harness-受控宿主深度原理解析-v1.0.md](./02-AI-Agent-Harness-受控宿主深度原理解析-v1.0.md)**
* **核心回答**：**Why Harness & How It Guards（为什么必须有 Harness、它如何解决生产环境 5 大痛点）**；
* **适用受众**：系统架构师、分布式可靠性工程师、安全架构师；
* **核心内容**：Harness 与图引擎的权责对齐、9 阶段不可穿透生命周期 Hooks 时序图、Fencing Token 与 CAS 乐观锁防脑裂数学模型、双进程物理密钥隔离、非幂等未知超时对账状态机。

### 3. 工程实施篇
* **[03-AI-Agent-端到端完全落地详细设计与工程实现指南-v1.0.md](./03-AI-Agent-端到端完全落地详细设计与工程实现指南-v1.0.md)**
* **核心回答**：**How & Where（怎么做、代码写在哪、表结构怎么建、API 怎么调、如何 100% 闭环落地）**；
* **适用受众**：核心开发工程师、测试工程师、DevOps/EvalOps 工程师；
* **核心内容**：包含 4 大套件的完整端到端微服务工程结构、PostgreSQL 物理 DDL、Harness 核心驱动代码、自包含 Hybrid RAG 检索代码、确定性 FakeProvider 离线闭环、EvalOps 自动化评测打分器与本地一键运行启动指南。

### 4. 分层专项深度解构系列 (Deep Dive Series)
* **[01-AI-Agent-L1-LLMOps网关深度架构与实战全景.md](./deep-dive/01-AI-Agent-L1-LLMOps网关深度架构与实战全景.md)** / **[English Deep Dive](./deep-dive/01-AI-Agent-L1-LLMOps-Gateway-Architecture-Deep-Dive.md)**
* **核心回答**：**Deep First-Principles（顶尖专家视角、底层 RFC 规范、微秒级观测、面试高段位应答应答与自愈指标）**；
* **适用受众**：基础架构工程师、网关/通信研发、高阶面试者、性能与可靠性调优专家；
* **核心内容**：
  * **一分钟高段位面试应答应答**：针对 LLM 网关稳定性与成本治理的标准话术；
  * **顶尖专家思维映射**：未被显式要求的深水区、原始 RFC/源码素材、专用工具链（llmperf/Toxiproxy）、独立于人的客观量化指标；
  * **四大子系统深度解构**：异构协议驱动适配器、SLA/Cost/429 动态加权路由与断路器、防越权防漂移 L1-L3 向量语义缓存、高并发流式背压与主动中断传播机制；
  * **生产落地自查清单**：高可用切换、附加延迟、缓存安全、审计对账与内存背压自愈验证。
* **[01-L1-Case-01-稳定性抖动与SLA容灾降级-RCA实战.md](./deep-dive/cases/01-L1-Case-01-稳定性抖动与SLA容灾降级-RCA实战.md)**
  * **核心痛点**：首字延迟暴增至 32s、HTTP 429 连环雪崩事故复盘与 200ms 无感降级；
* **[01-L1-Case-02-长连接背压吞吐瓶颈与内存OOM-RCA实战.md](./deep-dive/cases/01-L1-Case-02-长连接背压吞吐瓶颈与内存OOM-RCA实战.md)**
  * **核心痛点**：弱网慢客户端积压导致 32GB 内存打满 OOMKilled，内核级套接字监听与 HTTP/2 流控背压自愈；
* **[01-L1-Case-03-Token成本失控与语义缓存对账-RCA实战.md](./deep-dive/cases/01-L1-Case-03-Token成本失控与语义缓存对账-RCA实战.md)**
  * **核心痛点**：快时尚品牌首月 $187,000 天价账单事故，L1-L3 防越权语义缓存、Prompt Caching 对齐与 69% 成本压降。
* **[00-L1-LLMOps网关全局需求规格总说明书-v1.0.md](./deep-dive/specs/00-L1-LLMOps网关全局需求规格总说明书-v1.0.md)**
  * **核心定位**：Layer 1 网关总需求规格纲领（Master SRS），定义单进程模块化管道、全局认证隔离 (CFR-01)、W3C Trace 贯通 (CFR-02)、统一错误码规范 (CFR-03)、500ms 动态配置热加载 (CFR-04) 与优雅停机探针 (CFR-05)。
* **[01-L1-Sys1-异构模型统一驱动与适配器-需求规格说明书-v1.0.md](./deep-dive/specs/01-L1-Sys1-异构模型统一驱动与适配器-需求规格说明书-v1.0.md)**
  * **核心定位**：系统 1 工程基线，定义驱动 SPI、规范化 Canonical 契约、Tool Calling 双向转译、DeepSeek-R1 思维链提取与 P99 0.5ms 编解码延迟。
* **[02-L1-Sys2-多维智能路由与断路降级引擎-需求规格说明书-v1.0.md](./deep-dive/specs/02-L1-Sys2-多维智能路由与断路降级引擎-需求规格说明书-v1.0.md)**
  * **核心定位**：系统 2 工程基线，定义滑动窗口度量轮、多目标加权打分、1500ms 对冲双发（Hedged Requests）、三态熔断器与阶梯降级矩阵。
* **[03-L1-Sys3-防越权向量语义缓存与控费引擎-需求规格说明书-v1.0.md](./deep-dive/specs/03-L1-Sys3-防越权向量语义缓存与控费引擎-需求规格说明书-v1.0.md)**
  * **核心定位**：系统 3 工程基线，定义 L1~L3 递进式缓存、租户与 ACL 强制元数据硬过滤、Cross-Encoder 语义反漂移、Prompt Caching 物理对齐与毫秒级 Token 记账熔断。
* **[04-L1-Sys4-流式背压与长连接治理引擎-需求规格说明书-v1.0.md](./deep-dive/specs/04-L1-Sys4-流式背压与长连接治理引擎-需求规格说明书-v1.0.md)**
  * **核心定位**：系统 4 工程基线，定义多协议流式长连接、Socket 发送缓冲区监听、HTTP/2 流控帧反向背压抑制、固定环形缓冲 Zero-OOM 与客户端断线 5ms 级联取消。

---

## 历史归档与演进关系

* 原 `doc/kb/Harness.md` 已全面升级并演进为 `02-AI-Agent-Harness-受控宿主深度原理解析-v1.0.md`；
* 原 `doc/kb/AI-Agent-架构知识体系全景.md` 已全面补充并演进为 `01-AI-Agent-企业级架构知识体系全景指南-v1.0.md`；
* 整体知识体系为 [AI-Agent-Harness-企业级通用脚手架详细设计-v1.0.md](../../architecture/AI-Agent-Harness-企业级通用脚手架详细设计-v1.0.md) 提供上位架构支撑与理论基石；
* **业务落地映射**：参见 [01-跨境电商多AI-Agent生态体系业务架构与集成落地指南.md](../ecommerce/architect/01-跨境电商多AI-Agent生态体系业务架构与集成落地指南.md) / [English Edition](../ecommerce/architect/01-Cross-Border-ECommerce-Multi-Agent-Ecosystem-Architecture.md)，解构 6 大专业 Agent 协同与传统 OMS/WMS 系统共存方案。

