# 学生持续学习——AI Agent 群程序设计与工程脚手架 v1.0

| 属性 | 内容 |
|---|---|
| 日期 / 状态 | 2026-10-19；程序设计与脚手架实施规范评审稿，融合通用Harness架构与企业级脚手架设计；指导M03落地 |
| 直接上位设计 | [AI Agent群详细设计 v1.0](学生持续学习-AI-Agent群详细设计-v1.0.md)；本文将其职责/契约落实为程序组件、算法、工程和开发任务 |
| 上位通用架构 | [通用Agent-Harness参考架构与工程规范 v1.0](../architecture/通用Agent-Harness-参考架构与工程规范-v1.0.md)、[AI-Agent-Harness企业级通用脚手架详细设计 v1.0](../architecture/AI-Agent-Harness-企业级通用脚手架详细设计-v1.0.md) |
| 需求 / 架构 | [需求 v0.3](../requirements/通用Agentic学习与考试平台-系统需求规格说明书-v0.3.md)、[4A专项架构](../architecture/学生持续学习-多Agent与RAG-4A专项架构设计-v1.0.md)、[总体架构 v1.1](../architecture/通用Agentic学习与考试平台-4A总体架构设计-v1.1.md) |
| 业务范围 | 首次图谱路线共建、逐题作答、行为分析、讲解、四项更新、复习及恢复；公共知识运营内部另行设计 |
| 契约原则 | 沿用上位Schema/OpenAPI 1.0，不另造一组同名API；内部类名为建议实现名，不改变业务含义 |
| 技术方向 | Java微服务＋Python Agent Harness/Provider；Spring Cloud/Alibaba；LangGraph＋Harness；Kubernetes；DevSecOps/CI/CD |
| 版本策略 | 本文确定框架和候选兼容线；精确patch、镜像摘要、锁文件由G0/M01 PoC生成，经验证才成为部署基线 |

## 1. 阅读与交付边界

阅读顺序：需求→4A专项→通用Harness参考架构→脚手架详细设计→详细设计→本文技术/脚手架→组件/算法→数据/测试→开发任务。本文维持BA/AA/DA/TA追溯，但以开发顺序组织；不重复上位业务定义。


| 交付件 | 用途 | 本次状态 |
|---|---|---|
| 本文 | 用例到组件/函数/状态/事务/测试的程序规格 | 已编写，待评审 |
| [脚手架蓝图](ai-agent/programming/scaffold-blueprint.json) | 模块、运行入口、依赖、生成顺序、计划命令、验收 | 机器可读设计，不是生成器/已存在工程 |
| [Python端口模板](ai-agent/programming/templates/ports.py.example) | Agent/工具/模型/RAG/Repository抽象签名 | 模板；生成DTO后才能导入，非业务实现 |
| [pyproject模板](ai-agent/programming/templates/pyproject.toml.example) | 包/依赖/工具配置与入口 | 版本范围用于PoC求解，未生成uv.lock，不能直接作为生产锁定依赖 |
| [Python执行库DDL](ai-agent/programming/sql/001_agent_runtime.sql) | run/step/Inbox/工具/证据/提案表和约束 | 参考迁移；语法检查不等于真实迁移验证 |
| [Java协调库DDL](ai-agent/programming/sql/002_learning_coordination.sql) | 提交/快照/四项/租约/幂等/Outbox骨架 | 参考迁移；不覆盖完整题库/账务/个人资产领域模型 |
| [组件与场景用例](ai-agent/programming/component-cases.json) | 输入、预期行为、不变量、责任组件和需求关联 | 开发测试规格，非已运行集成测试 |
| [程序设计检查器](ai-agent/programming/verification/check_programming_design.py)与[检查记录](ai-agent/programming/verification/程序设计检查记录-v1.0.md) | 检查链接、格式、蓝图/用例及SQL语法 | 仅声明实际完成的检查 |

权威机器契约继续使用[JSON Schema](ai-agent/contracts/learning-agent.schema.json)和[OpenAPI](ai-agent/contracts/learning-agent.openapi.json)。修改协议必须同步版本与兼容评审；本篇伪代码不构成新接口。

## 2. 业务切片与四层落点（BA到程序）

| 切片 | 触发/前置 | 程序入口 | 输出/后置 | 异常出口 |
|---|---|---|---|---|
| SL-01 首次共建 | 产品发布、学生选范围 | Java RequestGoalDraft→bootstrap图 | 有版本的草案、先修和缺口 | 模型失败给规则草案；仍需学生确认 |
| SL-02 编辑确认 | 草案归属、expected_revision匹配 | Java EditDraft/ConfirmGoalBundle | 范围与初始路线同事务激活 | 冲突返回差异，未确认不生效 |
| SL-03 取题提交 | 有效Bundle、任务、题目许可 | Java CreateAttempt/SubmitAttempt | 最终答案、评分/待判、快照和四项pending | 行为失败不阻断合法最终答案 |
| SL-04 分析更新 | 已提交、任务授权/预算 | Python attempt图 | 分析/讲解、Java四项收据及下一步 | 分支独立、no_change/partial可见 |
| SL-05 复习/持续 | 到期或主动进入 | Java ReviewScheduler→题目→SL-03/04 | 复习证据与当前安排 | 无历史称回顾；过期任务校验/迁移 |
| SL-06 改目标/恢复 | 用户修改、迟到快照、退出或故障 | control、扫描器、新版本run | 当前输入重评/恢复，无重复副作用 | 旧输入superseded；费用unknown对账 |

BA：学生持续学习与授权；AA：第4～9章；DA：第10章与DDL；TA：第3、11～12章。UI/UE遵守上位第7.4节：答案保存先反馈，观察/推断分开，四项异步状态及恢复按钮清晰。

## 3. 技术选型、兼容和框架基线

### 3.1 决策等级

“选定框架”表示本文推荐实施，不表示已安装/压测；“候选系列”用于G0锁具体patch；“生产锁定”必须同时有BOM/uv.lock、镜像摘要、支持窗口、许可证、安全扫描及PoC证据。本次不伪造这些产物。

| 领域 | 本文选定方案 | 候选系列 / 验证要求 |
|---|---|---|
| Java运行/构建 | JDK 21 LTS，Maven Wrapper，Spring Boot/Cloud/Alibaba | Boot 4.0.x＋Cloud 2025.1.x＋Alibaba 2025.1.0.0起点；按实际支持补丁成组PoC；不单独追最新Boot |
| JavaHTTP/认证 | Spring MVC、Validation、Security OAuth2 Resource Server；Gateway独立应用 | REST边界、工作负载JWT；长推理不占MVC请求线程；不引入Java侧第二套Agent编排 |
| Java持久化 | Spring JDBC/JdbcClient、声明式事务、Flyway | 显式SQL便于CAS/Outbox；避免首次同时引入多种ORM，驱动随BOM/支持线验证 |
| Java消息/测试 | Spring AMQP、JUnit、Testcontainers、ArchUnit | RabbitMQ协议统一，真实PostgreSQL/消息测试，版本随Boot兼容和工具支持锁定 |
| Python运行/包管理 | CPython 3.14常规GIL构建，uv，src布局 | 当前受支持维护线；检查所有原生wheel/依赖，不默认free-threading；3.13只作为有证据的兼容回退并单独批准 |
| PythonHTTP/类型 | FastAPI、Uvicorn、Pydantic 2、pydantic-settings | 内部API/健康检查；严格DTO＋JSON Schema独立校验；同步库不能阻塞事件循环 |
| Agent编排 | LangGraph 1系列及PostgreSQL持久化适配；自有Agent接口 | 图按run版本固定；框架负责执行/checkpoint，不替代业务事务/授权/幂等 |
| Python数据 | SQLAlchemy 2.1异步Core＋psycopg 3，Alembic | SQLAlchemy的2.0维护线仅作为兼容退路；每任务独立事务/连接，不共享并发AsyncSession |
| Python消息/HTTP | aio-pika、HTTPX、asyncio | robust连接只是连接恢复，业务仍需Inbox/Outbox；HTTPX共享有界客户端与超时 |
| 模型 | 自有ProviderPort＋提供者SDK适配器；MockProvider先行 | 用户协议范围/ModelProfile仍需批准；LLM只有Provider进程可解密密钥，普通Agent不导入厂商SDK |
| RAG | PostgreSQL关系/词项＋术语词典＋pgvector；Python融合/证据装配 | 中文分词方案需查询集验证；不默认默认英文分词能满足法考；暂不增加独立图库/整套RAG编排框架 |
| 数据/消息/缓存 | PostgreSQL、RabbitMQ、Valkey、S3兼容对象存储 | 沿主架构方向；精确patch/驱动/插件在G0验证，不把缓存当业务账本 |
| Python工程质量 | pytest/pytest-asyncio、Ruff、mypy、jsonschema、Testcontainers | DTO与契约一致；性质/故障/权限测试；真实模型评测单独预算和队列 |
| 观测 | OpenTelemetry、结构化JSON日志、Prometheus/Grafana | 统一trace/run/step/cycle关联，GenAI语义属性锁版本，不自动采集全文 |
| 部署/交付 | Docker/OCI、Kubernetes、Kustomize，Argo CD作为GitOps CD方案 | CI用平台中立任务规格接入现有Runner；生产发布走受保护配置库、签名镜像和环境晋级 |

未默认引入Celery作为跨语言协议、MCP/A2A、Service Mesh、Seata、独立搜索集群、自动多提供者切换。将来有明确需求时单独ADR和兼容/安全验证；不能因为采用Spring Cloud Alibaba就启用其全部组件。

### 3.2 官方核验与兼容取舍

2026-10-18查询：[Spring Cloud兼容表](https://spring.io/projects/spring-cloud/)说明2025.1系列的Boot支持关系；[Alibaba版本表](https://sca.aliyun.com/en/docs/2025.x/overview/version-explain/)给出2025.1.0.0/2025.1.0/4.0.0及相关组件映射。因此优先在共同覆盖的Boot4.0系列验证，不能根据Cloud支持Boot4.1就推断Alibaba全部兼容。表中的最初版本仅是映射证据，不是应长期冻结的安全补丁。

[Python支持状态](https://devguide.python.org/versions/)显示3.14处于bugfix、3.13处于security；本篇推荐3.14，需与AI库实测。上位详细设计仅要求受支持Python线；主架构旧技术表的3.13将以本推荐及PoC决策明确解释，不能无声替换生产环境。

[FastAPI异步说明](https://fastapi.tiangolo.com/async/)、[Pydantic文档](https://docs.pydantic.dev/latest/)、[uv布局](https://docs.astral.sh/uv/concepts/projects/layout/)作为HTTP/类型/工程依据；[SQLAlchemy异步说明](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html)、[Spring JDBC](https://docs.spring.io/spring-framework/reference/data-access/jdbc/core.html)作为数据访问依据。

[LangGraph持久化](https://docs.langchain.com/oss/python/langgraph/persistence)不保证领域副作用一次；[RabbitMQ确认机制](https://www.rabbitmq.com/docs/confirms)区分publisher confirm和consumer ack；[aio-pika](https://docs.aio-pika.com/)提供async客户端；[Argo CD](https://argo-cd.readthedocs.io/en/stable/)作为GitOps运行依据。引用是选型输入，不代表本组合经过联调。

### 3.3 G0技术锁定清单

必须输出dependency-lock-manifest：JDK发行/patch、Maven Wrapper/hash、Boot/Cloud/Alibaba BOM、Java依赖树及收敛检查、Python/uv/uv.lock/hash、数据库/扩展/消息/缓存/身份版本、镜像平台与digest、K8s版本、ModelProfile、许可证及支持到期Owner。上限范围只用于求解，CI必须frozen锁文件；生产不得使用latest、动态快照或未审核patch。

兼容试验：Java启动/注册/配置/鉴权/SQL事务/AMQP→Python消费/严格校验→LangGraph持久化/崩溃恢复→HTTP提案及fencing→pgvector/词项授权查询→trace贯穿→旧图检查点/旧消息兼容。失败只调整相应适配/版本，不自动换业务协议。

## 4. 工程脚手架（Scaffold）设计

### 4.1 仓库与微服务运行单元

遵循云原生与微服务领域能力命名规范，项目杜绝宽泛的语言目录命名，采用标准领域能力微服务结构：

```text
services/
  cogniva-learning-core/               # [Java] 目标/答题事实/四项收据/计划正式生效事务
  cogniva-knowledge-service/           # [Java] 已审知识母本/题库/图谱版本与审核发布
  cogniva-platform-service/            # [Java] 工作负载鉴权/租约/预算预占与对账
  cogniva-gateway-bff/                 # [Java] 学生接入/会话/查询与状态投影
  cogniva-learning-agent/              # [Python] 核心 Agent Harness 运行时 (包名: cogniva_agent)
    pyproject.toml / uv.lock / Dockerfile
    migrations/                        # Alembic 执行库迁移 (runs, steps, checkpoints, leases, inbox, outbox)
    src/cogniva_agent/
      domain/                          # 纯净领域模型 (Run, Step, Event, Session, IntentProposal, 规则路由)
      ports/                           # 六边形抽象端口 (ModelPort, PolicyPort, BudgetPort, CheckpointPort, ReceiptPort, EvidencePort)
      harness/                         # 宿主控制环 (advance 状态机, 9阶段 Hook, 租约fence, 保护项装配, 对账器)
      agents/                          # LA-01 协调器及 LA-02~05 叶角色业务逻辑
      workflows/                       # LangGraph 确定性图 (explain_flow, practice_flow, replan_flow)
      adapters/                        # 适配器 (FastAPI 入口, SQLAlchemy 2 异步Checkpointer, AMQP, Fake/ProviderClient)
    tests/                             # unit / contract / harness (含故障注入)
  cogniva-model-provider/              # [Python] 独立大模型出网网关与密钥代理 (包名: cogniva_provider)
    pyproject.toml / Dockerfile
    src/cogniva_provider/
      domain/                          # ModelProfile, 价格表版本, 计数器
      ports/                           # 统一大模型供应商接口
      adapters/                        # FakeProvider (测试用) 与真实厂商 SDK 适配器 (出网边界)
      server/                          # Provider 内部 HTTP/gRPC 出网代理服务
    tests/
contracts/                             # 冻结的 OpenAPI 契约、JSON Schema、工作流目录与生成器清单
infra/local/                           # 本地 Docker Compose (PG+pgvector, RabbitMQ, Valkey, OTel)
infra/k8s/{base,overlays}/             # K8s 部署清单 (test / stage / prod)
pipelines/                             # 平台中立 CI 流水线与质量门禁
scripts/                               # 契约生成、冒烟测试、故障重投演练脚本
```

### 4.2 Harness 宿主控制环与 9 阶段生命周期 Hooks（核心工程规范）

脚手架遵循上位 [《AI-Agent-Harness企业级通用脚手架详细设计 v1.0》](../architecture/AI-Agent-Harness-企业级通用脚手架详细设计-v1.0.md) 确立的 **“LangGraph 作为图执行引擎，Harness 作为外层受控宿主（Control Ring & Host）”** 铁律。

```text
advance(run, fencing_token):
  load pinned release and durable state
  verify lease, tenant, cancellation, deadline, authorization freshness
  reconcile any pending or unknown external operation before resending
  select ready step from approved workflow
  assemble protected context; resolve approved skills; reserve model budget
  choose deterministic rule OR invoke approved model
  validate candidate schema, evidence and legal action set
  for each selected action within bounded concurrency:
    verify dependency, latest scope, cancellation and resource revision
    authorize action; reserve its budget
    persist tool/delegation intent with stable operation_ref
    execute via adapter, record result OR unknown status
    validate output, sanitize untrusted content, record usage/receipt
  checkpoint durable progress
  evaluate done / wait / no-progress / budget / deadline / cancellation
  finalize atomically OR persist wait / enqueue next bounded step
```

#### 9 阶段生命周期拦截器规范（不可绕过）：
1. **`on_run_load`**：加载不可变版本 Profile，校验租户、租约（lease）与删除墓碑（Tombstone），拦截已被注销或越权的任务；
2. **`before_context`**：校验学生授权时效与目的（purpose），重读必要事实，剔除越权片段；
3. **`before_model`**：Token 计数预测、出网目的地检查、原子预占模型预算，检查 Run 是否已被用户取消；
4. **`after_model`**：校验结构化 JSON Schema、记录实际 Token/用量、拦截非法提权，处理拒答；
5. **`before_action`**：**安全核心闸门**。只有宿主能从模型候选构造 `AuthorizedToolCall`，模型自己输出 `permit=true` 必须被代码阻断；
6. **`after_action`**：持久化全局唯一业务操作键（`operation_ref`）、哈希校验、处理网络未知超时（标记 `unknown`）；
7. **`before_checkpoint`**：使用单调自增 `fencing_token` 与 CAS 乐观锁持久化状态，旧 Worker 脑裂写操作立即拒绝；
8. **`before_finalize`**：汇总已达成目标与待确认/未完成项，生成聚合收据；
9. **`after_finalize`**：Outbox 异步发布终态与脱敏审计日志。

#### 核心机制落地：
- **进程密钥物理隔离**：`cogniva-learning-agent` 绝对不持有大模型 API Key，仅通过内部 RPC/HTTP 与 `cogniva-model-provider` 通信；本地测试默认注入 100% 确定性的 `FakeProvider`；
- **操作幂等与未知对账**：每次工具执行与外部提案提交前必须持久化 `operation_ref`；遇网络超时标为 `unknown`，由专职对账器（Reconciler）进行指数退避查询，严禁盲目自动重试非幂等写；
- **长上下文保护项**：系统指令、学生当前否定句（如“周末不学民法”）、当前核心目标为最高优先级保护片段，禁止简单“截断最近N轮”；输出显式 `ContextManifest`；
- **原子预算守恒**：父 Agent 预占总预算，子 Agent 委派时原子切分子额度，`子分配 + 父已花费 <= 批准总上限`；
- **死循环/无进展熔断**：步数上限、超时、预算耗尽以及“输入/动作/参数哈希连续 3 次无新状态变化”强制熔断；
- **双向 Stub 生态**：内置 `JavaStub`（供 Python 模拟业务上下文与收据）与 `AgentStub`（供 Java 模拟 Agent 响应）。

### 4.3 Composition Root与依赖方向

FastAPI lifespan创建Settings→契约/Prompt/Policy/Graph清单校验→HTTP/SQL/消息连接池→适配器→AgentRegistry/GraphRegistry→用例服务；关闭时停止接新任务、标记readiness=false、等待有界在途、flush投递状态、释放租约/连接。导入模块不能开网络或自动迁移DB。

- **依赖单向流动**：Domain（纯业务/无三方依赖）← Ports（接口定义）← Harness（控制环）← Workflows/Agents ← Adapters（具体技术实现：FastAPI, SQLAlchemy, LangGraph, ProviderClient）。
- **绝对禁止反向依赖**：禁止 Agent 依赖 SQLAlchemy、HTTPX、厂商 SDK 或读取环境变量中的密钥。Repository 不持模型调用，模型不在数据库事务中等待。
- **Java 侧边界**：JavaController→ApplicationService→DomainPolicy/RepositoryPort；JDBC/AMQP实现位于infrastructure。请求用户与内部工作负载安全链分开，内部DTO不能作为学生公开接口。使用构造器注入，测试替换端口而非修改全局单例。

### 4.4 标准启动与开发任务（未来生成工程的命令契约）

以下命令目标由脚手架阶段通过根 Makefile 与 scripts 统一实现并逐条验收：

| 计划目标 | 内容 / 成功条件 |
|---|---|
| make bootstrap | 核验JDK/Python/uv/Maven Wrapper；按锁文件安装；没有锁则进入G0锁定，不默默联网升级 |
| make contracts | 验证Schema/OpenAPI并生成Python DTO/Java DTO；生成清单记录输入hash/工具版本，CI检测漂移 |
| make dev-up | 启动本地PG/RabbitMQ/Valkey/对象存储与测试身份，端口仅本机；等待健康；不包含生产模型密钥 |
| make migrate | Java Flyway、Python Alembic、框架checkpoint安装任务分别串行执行；不由每个Pod启动时抢迁移 |
| make seed-demo | 仅合成知识、题目/答案、用户、授权、固定FakeProvider；可重复，无真实版权材料 |
| make run-java / run-agent-api / run-worker / run-provider | 独立启动；内部地址/健康端口从Settings加载；Agent使用FakeProvider或Provider代理 |
| make test-unit / test-contract / test-integration | 无网单测（<5s）、契约校验、真实本地DB/消息集成分开；失败非零退出 |
| make smoke-learning | 一次完整任务、四项收据、查询状态及trace验证 |
| make fault-redelivery | 投递重复消息（10次）、杀Worker恢复测试、旧fencing回执冲突测试，确认不重复写入 |
| make package / deploy-stage | 构建签名镜像/SBOM和Kustomize清单，预发部署；生产需受保护GitOps流程 |
| make dev-down | 停本地服务，默认保留卷；删除数据必须显式额外选项 |

### 4.5 脚手架最小链路验收与非功能性硬指标

使用合成Submission/event→Java事务Outbox→RabbitMQ→PythonInbox/run→规则路由到LA-02 FakeProvider→ProposalDelivery→Java验签/租约/版本/采纳→四项规则结果→GET cycle/run。

必须满足以下 6 大非功能性（S-NFR）硬指标才可判定脚手架就绪：
1. **S-NFR-01 安全零信任**：Worker 进程 0 密钥配置；`before_action` 成功拦截模型伪造的 `permit=true`；审计日志中学生 PII 自动脱敏；
2. **S-NFR-02 高可靠幂等与自愈**：同一作答消息重复投递 10 次，业务收据与事实仅变更 1 次；Worker 进程在任意 Step 被强杀后重启自动从 Checkpoint 恢复；旧租约 Worker 的写操作 100% 被 CAS Fencing 阻断；
3. **S-NFR-03 本地确定性**：依赖 FakeProvider 与 Synthetic 数据，全部单元测试与契约测试在断网机器上 100% 通过，耗时 < 5 秒；
4. **S-NFR-04 并发有界**：全链路异步非阻塞（FastAPI + asyncpg + HTTPX），单 Run 子 Agent 最大递归深度 `max_depth <= 2`；
5. **S-NFR-05 可观测审计**：完整关联 trace/run/step/operation_ref，高风险提案审计日志不可采样；
6. **S-NFR-06 架构纯粹**：替换 LangGraph 或底层模型驱动不影响 Agent 领域层与意图规则。


## 5. 类型、端口、错误和执行上下文

### 5.1 类型映射与兼容

权威为JSON Schema Draft2020-12，API为OpenAPI3.1；Python生成Pydantic2 DTO（frozen、extra=forbid，禁止bool当int等宽松转换），Java生成records/POJO＋Bean Validation及必要自定义约束。JSON Schema仍作边界独立验证，生成器不能完整表达allOf/if/then时用显式校验器补足，不能删约束迁就生成器。

JSON timestamps→timezone-aware datetime / Java Instant；revision/seq→整数，范围按Schema；外部引用字符串与数据库UUID是两层：内部id UUID，public_ref TEXT UNIQUE映射。不能把样例run_01强制解析UUID，也不让数据库主键泄漏权限含义。金额/Token账本由平台整数最小单位或Decimal处理，不用float结算。

Schema封闭字段下，新增字段先发布接收端兼容多版本，再发送新minor；新增枚举、必填或含义变化评审，破坏升级新major。上下游共享同一输入hash规范，采用固定键序、UTF-8、明确null/缺失语义的canonical JSON；幂等payload中包含影响执行的字段，不包含trace瞬时头。

### 5.2 六边形端口体系（Ports Architecture）

脚手架遵循六边形架构（Ports & Adapters），领域层与 Harness 内核通过强类型抽象端口与外部技术实现解耦：

| 端口名称 (Port) | 核心方法规格 | 职责与安全边界 |
|---|---|---|
| **ModelPort** (ModelGatewayPort) | reserve / submit / query / settle(spec) → ModelResult | 模型调用抽象；SDK仅存在于独立Provider；超时未知记录 `usage_unknown` |
| **PolicyPort** (ContextResolverPort) | resolve(refs, purpose, auth_ref) → AuthorizedContext | 校验学生授权与时效；签发最小必要上下文，未授权操作失败关闭 |
| **BudgetPort** | reserve / allocate / record_usage / settle / release | 模型预算与费用管理；多Agent委派时原子切分子预算，防止并发超支 |
| **CheckpointPort** (RunRepository / UoW) | get / save_checkpoint / CAS_transition(fence) | 状态检查点与分布式CAS；校验单调自增 `fencing_token` 防脑裂 |
| **ReceiptPort** (ProposalPort) | submit_proposal(kind, payload, operation_ref) → Receipt | 向Java业务核心提交候选提案并获取正式收据；200不等于全部更新 |
| **EvidencePort** (EvidenceRetrieverPort) | retrieve(query, auth_scope) → EvidenceSet | 知识与证据检索；仅在授权范围内返回带来源/版本/有效期的证据 |
| **ToolPort** | execute(invocation, verified_context) → ToolResult | 受控动作执行；必须具备持久化 `operation_ref` 与白名单权限检查 |
| **LeasePort** | claim / renew / release(run_ref, expected_token) | 分布式租约操作；以Java/数据库租约服务为时钟权威 |
| **AgentPort** | execute(invocation, agent_context) → RoleOutput | LA-01～05 领域实现规范，返回类型化提案，绝不直接写业务表 |

详细签名见 [端口模板](ai-agent/programming/templates/ports.py.example)。接口采用全异步声明（`async/await`），副作用不得隐藏在属性访问或序列化过程中。上下文不可变；运行进度仅在独立状态与检查点中更新。


### 5.3 AgentContext与图状态

AgentContext包含Invocation、VerifiedIdentityRef、授权上下文、版本化Policy、PromptManifest、ModelProfile、Deadline、BudgetView、ToolRegistry只读句柄、trace引用。正文/检索证据按来源分区；密钥、全库连接和Java领域Repository不进入Context。

GraphState只存run/epoch、input_refs、各步骤输出引用、收据、支路状态和错误摘要；大正文在受控短期对象/EvidenceSet，通过引用读取。并行字段分开：analysis_ref、explanation_receipt、personal_receipt、plan_receipt；不能并发append同一可变messages列表。

Reducer采用按step_key的不可变映射合并，同一step_key不同payload_hash视冲突；不采用最后写入覆盖。所有分支只返回自己拥有的delta，汇总节点读取Java当前cycle状态确认，不凭图内字符串声称四项完成。

### 5.4 错误类型与传播

内部DomainError(code,retryable,source,correlation_ref,safe_details)映射上位Error。ContractViolation/AuthorizationDenied/VersionConflict/BudgetExceeded/DeadlineExceeded/EvidenceInsufficient/ProviderUnavailable/ProviderUnknown/LeaseLost分别处理。不得catch Exception后全部转换success/no_change。

API映射沿上位400/401/403/404/409/422/429/503；消息非法/越权进入隔离或工单，不热循环requeue；模型结构错误有限修复；语义不足合法降级；unknown进入对账。CancelledError必须传播或明确清理后重抛，不能误当可重试模型失败。

## 6. 工作流和调度程序

### 6.1 执行入口和任务认领

```text
RunService.create(request, identity):
  verify_identity_and_scope(request)
  validate_contract_and_workflow_required_refs(request)
  in Python UoW:
    replay = find_idempotency(principal, operation, goal, key)
    if replay: compare_payload_hash_or_conflict(); return original_receipt
    insert run(status=queued, version_manifest, input_refs)
    insert local dispatch item / inbox linkage
    save idempotency receipt
  return 202 run_ref
```

AMQP路径不重复调用HTTP造成双登记：消费者在同一个本地事务写Inbox和run/dispatch，提交后ack。Worker周期扫描queued/partial可恢复项，短事务FOR UPDATE SKIP LOCKED认领本地dispatch，事务外向Java claim租约；领不到则退避，不能持SQL锁等HTTP。领到后CAS镜像epoch，运行时按ttl/3心跳；租约疑似失效立即停止新副作用。

Java租约服务clock为到期权威，Worker用本地monotonic计算安全余量，不能根据客户端时间决定租约有效。已有运行者未过期不可强抢；取消由Java撤销run授权/标cancel并阻止提案和新Invocation。

### 6.2 G1 Bootstrap图节点规格

| 节点 | 读 / 写 | 条件与副作用 |
|---|---|---|
| authorize | input_refs→context_ref | 授权/版本/期限失败终止 |
| load_scope | context→subgraph/resource_refs | 只读Java母本，记录缺口 |
| deterministic_seed | subgraph→candidate_ref | 拓扑排序/先修闭包及资源，循环为缺口 |
| propose_plan | seed→PlanOutput引用 | 按需LA-04；失败用规则候选并披露 |
| validate_draft | candidate→validation_ref | Java预校验；最多一次有界修复 |
| persist_draft | validated→draft_receipt | Java提案命令幂等保存草案，不激活 |
| finish | receipt→run状态 | 学生编辑/确认仍由Java，不占长期Worker |

上位通用ProposalRequest(kind=plan, mode=initial)在Java路由到保存草案用例，非初始计划激活。学生确认API验证具体修订，Python没有代签确认工具。编辑后新草案版本使旧候选失效，不能重放模型结果覆盖学生选择。

### 6.3 G2 Attempt图节点规格

| 节点 | 必需输入 | 输出 / 后继 |
|---|---|---|
| authorize | AttemptGraded/input_refs | 当前授权与题目/评分/范围修订；失效→superseded/取消 |
| extract_features | 冻结行为快照、quality | FeatureRevision；缺失→有限特征 |
| analyze | 评分/特征/审核映射/历史 | LA-02/规则Analysis；insufficient可继续已审辅导 |
| explain | analysis可选、标准答案、证据 | LA-03→Java explanation receipt；与personal独立 |
| personal | 有资格证据、当前个人版本 | LA-05/规则→Java两项收据及确认watermark |
| plan | 个人确认watermark、范围/时间 | LA-04或规则→Java学习/复习两项收据 |
| collect | Java实际cycle当前状态、各支路 | completed/partial/failed及下一步引用 |

关键并行实现：explain与personal/plan各自支路内部捕获可处理异常并返回BranchResult，非业务可处理异常留给统一故障处理；不能简单TaskGroup任一失败取消所有支路。两个支路均返回后collect，但成功支路的Java结果可立即显示，不等待另一支路才落库。全局取消/租约失效则对所有未开始副作用停止。

分支失败不阻止能独立完成的确定性证据记录。personal不可产生确认水位时，plan等待/失败或采用批准旧水位降级并说明；不假称使用新画像。相同Submission多快照按最新允许版本产生新analysis run，logical_cycle不变；旧版本结果不采纳。

### 6.4 G3 Review与G4 Assist

ReviewScheduler在Java事务租约认领到期logical_task→校验范围/内容/权益→创建Attempt；实际答题提交复用G2；Python的review注册为attempt图的模式别名，不另外调度/评分。主动回顾无历史设mode=review但不产生虚构遗忘记录。

AssistController规则路由固定命令→必要时LA-01分类→clarify/assist/plan_change；辅导走LA-03，范围或预算变化保存草案/待确认。会话thread绑定用户/目标，历史裁剪保留关键版本和限制；对话不能调用任意外部Agent。

### 6.5 状态转移、检查点和重入

状态沿上位queued/running/waiting_input/partial/completed/failed/cancelled/superseded，转移通过CAS(expected_revision,allowed_from,fencing)。failed/cancelled/completed/superseded为历史终态，人工重试创建child_run；partial可queued恢复未完成步骤。每次转换记录from/to/reason/actor及版本，不直接update任意status。

检查点thread使用run UUID＋epoch命名空间，防旧Worker在新epoch写同一执行分支；框架状态不能成为业务事实。新epoch从已登记的兼容checkpoint重建，但先读Java提案收据/周期状态和当前授权，已采纳步骤跳过副作用。旧epoch晚写检查点可成为孤立记录，不能覆盖当前registry指针或Java事实。

图版本/Prompt/Policy/Schema固定于run；部署保留旧版本Worker池，不能兼容时显式暂停/迁移并记录映射。恢复可能重跑节点，所有副作用查幂等收据；迁移检查点表由框架适配器安装，不手写猜测其内部DDL。

### 6.6 执行租约与跨服务限制

Java学习核心execution_fence提供claim/renew/release/get；claim只在不存在/到期/已释放且expected_token匹配时递增，renew验证holder/token且未过期，release不允许把旧epoch释放成新epoch。Python写本地进度也检查镜像token。

Java学习核心采纳提案在同一事务锁定租约及目标版本并写业务结果。Java平台服务Invocation begin通过受控LeasePort查询权威租约，但跨服务查询不构成分布式原子事务；已获准的在途模型请求可能在取消/租约到期后完成并产生费用，必须标在途并审计。新Worker复用同一逻辑Invocation而非再付费重调；真正防重复依靠平台(run,step,logical_call_index)唯一键和reserved→running CAS，不承诺供应商端恰好一次。

## 7. 五类Agent内部程序与模型执行

### 7.1 统一AgentExecutor算法

```text
execute(invocation, verified_context):
  strict_validate(invocation); ensure_role_registered()
  load_pinned_prompt_policy_model(); assert_scope_deadline_budget()
  inputs = role.load_inputs_via_allowed_tools()
  prepared = role.prepare_deterministic(inputs)
  if role.can_complete_by_rules(prepared): return validate_rule_output()
  payload = assemble_trusted_and_untrusted_sections(prepared)
  payload = trim_to_budget_preserving_permissions_versions_facts(payload)
  call_index = allocate_next_logical_call_in_local_transaction()
  persist call_intent(hash, call_index) before any network call
  result = provider_port.reserve_and_submit_or_lookup_same_call(payload)
  if unknown: persist unknown; stop automatic new calls; return pending_reconciliation
  parsed = strict_parse_json_and_schema(result)
  if invalid and repair_allowed: one_budgeted_new_call_with_error_summary()
  output = role.validate_semantics(parsed, inputs)
  persist output_ref/hash/version; return output
```

同一逻辑调用重入复用持久化call_index/hash；只有明确批准的修复/重试才增加index，受父run总请求数限制。模型输出不能包含自报工具授权；执行器先验证工具名/参数/context，再通过受控端口执行；多轮工具循环计入相同run步骤、工具与费用上限。

### 7.2 角色专属实现

LA-01的局部需求、C4视图、意图/计划契约和注册模板详见[LA-01独立设计](agents/LA-01-学习协调Agent-需求与C4详细设计-v1.0.md)。

| 角色 / 建议类 | 程序步骤 | 必须的语义校验 |
|---|---|---|
| LA-01 IntentRouterAgent | rule_router→读取上下文→必要模型分类→allowed_workflows交集→澄清/调批准子图 | clarify必须有具体问题；不得新建未注册流程；目标与授权来自服务端 |
| LA-02 AttemptAnalysisAgent | 读Grade/Feature→审核选项映射→筛选历史→有限假设→证据/反证关联 | 分数无修改字段；假设节点在允许子图；缺映射不能断言具体概念；quality不可掩盖 |
| LA-03 TutorAgent | 精确答案/解析→RAG→充分性→生成段落→引用/答案校验→保存建议 | answer_revision一致，引用允许且支持；不符合则退已审解析/工单，不传未经校验正文给学生 |
| LA-04 LearningPlannerAgent | 读范围/先修/资源→规则骨架→LLM可读候选→拓扑/预算/资源预检→提案 | initial.requires_confirmation=true；任务引用真实、无环、范围/时间不越权；日期由Java策略算 |
| LA-05 PersonalEvidenceAgent | 读资格/独立标记→关联个人记录→汇总正反证→提候选→Java计算/保存 | 无mastery_probability权威字段；反复同题不当独立证据；不创造人格标签或自动收藏正文 |

每个角色的输入来源/工具/模型/错误沿用上位第4章，提示沿用[角色模板](ai-agent/agent-prompts-v1.0.md)。开发不得在角色内部绕过统一执行器直接用SDK调用模型。

### 7.3 Provider程序、结构化与流式

ProviderAPI202前先持久登记execution，关联唯一Invocation及payload hash；dispatcher读取待执行记录→向Java平台begin→获准后读取加密payload和当前所需密钥→适配器request→持久结果/usage→settle。外呼前写running，崩溃后查供应商结果，不将running直接改queued重发。

ModelAdapter能力接口：build_request(profile,payload)、invoke(timeout,cancel)、normalize_response、normalize_usage、query_by_provider_request_id（可不支持）。支持的供应商由配置白名单/ModelProfile启用；无原生JSON Schema可严格解析一次修复，仍不满足则禁用相应Agent能力，不静默换提供者。

流式Token只作内部临时缓冲；正式教学段落校验后才经Java发布。流断开不说明模型未收费/未完成；按Invocation查询和结算。错误按rate_limit/timeout/auth/context_length/invalid_output/result_unknown映射，供应商错误正文脱敏。

### 7.4 上下文和提示裁剪

优先级：授权/禁止事项→题目/标准答案/输入版本→当前任务与必要证据→支持/反证→相关历史→聊天。必须为输出和工具预留Token；裁剪不能将弱证据限制删掉只留结论。关键项本身超限则分解或降级，不能“截断到能调用”。

PromptManifest包含模板hash、变量Schema、output_schema、模型能力、tool allowlist和评测引用；应用启动验证清单，run固定版本。提示内容、模型设置和检索配置分别版本化，严禁只改热配置文本导致不可重现。

## 8. 工具、Java交互与持久投递

### 8.1 工具适配器

ToolRegistry注册(name,input_schema,output_schema,allowed_roles,purpose,side_effect,deadline,max_bytes)。ToolExecutor验证上下文中允许工具、角色/目标、剩余预算和严格参数后调用；ToolResult按tool_name分派对应View。HTTPX使用有界全局连接池，request附工作负载短期Token、correlation/idempotency，但Token不进入图/checkpoint或日志。

只读工具可有限网络重试；写提案/Invocation必须持久化幂等意图再调用。分页page_token不透明、绑定context/查询/版本，不能接受另一用户cursor；输出过大返回next_page_token而非静默截断。嵌套arguments中context_ref必须与外层一致，服务端不信任模型传另一授权引用。

### 8.2 ProposalDispatcher与Java用例

```text
produce_proposal(output):
  in local UoW:
    build proposal with pinned input_refs/policy/fence
    insert delivery(logical_key, hash, payload_ref, pending) or replay
  dispatcher sends same proposal_id + Idempotency-Key
  on timeout: retain pending; retry/query same logical command
  on receipt: persist receipt, notify workflow; never infer acceptance from HTTP timeout
```

JavaApplyProposal先按principal/operation/goal/key查幂等，再比payload_hash；同键不同内容409。新提案在事务内验证当前租约、授权、Bundle/版本、资格/业务约束，更新相应结果并保存receipt/Outbox。重复已采纳命令返回原收据是历史查询，不重新执行副作用；查询仍要验证当前身份是否可读。原收据不代表输入仍适合下一步，规划等后继重新读当前水位。

initial plan路由SaveGoalDraft，不激活；personal给知识/画像两项结果，plan给学习/复习两项结果；analysis/解释另存。no_change仍必须有reason_codes。HTTP200的rejected/conflict不能当完成，409按新状态创建新proposal，不改旧payload重发旧键。

### 8.3 消息与Outbox程序

Publisher短事务SKIP LOCKED认领Outbox→事务外publish persistent message＋confirm→成功标sent，超时保留unknown/pending重试。同一事件可多次发布，event_id不变。消费者写Inbox/run/dispatch同事务，成功后ack；重复同hash返回已登记，重复不同hash进隔离。publisher confirm只证明Broker处理，不代表业务消费者完成。

Java/Python都需要自己的Outbox或持久dispatch，不能先ack消息再只在内存启动协程。消息仅带版本化信封和payload_ref，消费者拉取时重新授权。重试等待用数据库next_attempt_at/租约调度，死信带原因/重放审计；不得无限立即requeue占满正常队列。

## 9. RAG与教学算法程序

### 9.1 检索组件与算法

| 组件 | 输入→输出 | 实现要点 |
|---|---|---|
| ScopeResolver | context/目的→allowlist ticket | Java当前授权/产品/时间/许可/manifest，票据短期有效 |
| QueryNormalizer | query＋词典版本→关键词/别名/原查询 | 保留原意与适用时间，不把查当年题改成现行法 |
| ExactLookup | 题目/答案引用→审核记录 | 绕过模糊召回，学生提交前不暴露答案 |
| LexicalRetriever | 允许集合＋术语→带排名候选 | 中文预分词/术语展开；参数化SQL |
| VectorRetriever | 同允许集合＋query embedding→候选 | profile/维度一致，先过滤/选择性精确扫描策略 |
| RankFusion/Reranker | 候选→有序PassageRevision | 先去重再RRF，可用批准重排器；目的地许可 |
| GraphExpander | 允许关系/深度/节点→相邻证据 | 循环visited、边类型和版本限制；不扩学生有效范围 |
| EvidenceAssembler | 候选＋用途/限制→EvidenceSet | 引用/定位/hash、权威与个人证据分区、Token预算 |
| EvidenceValidator | 结论/证据→充分/不足/冲突 | 结构/适用性可程序检验，语义支持另评测 |

RRF：对每个retriever的去重排名，score(p)=Σ 1/(k+rank_i(p))，rank从1开始，k沿pilot=60；缺席不贡献分数，同revision在同通道仅计一次。分数不是可信概率；足证据必须有适用依据/审核等级与无未解决冲突，不能只设“向量分数大于x”。

缓存键按上位第6.3节，canonical query/hash、manifest、授权/许可版本、索引代际与个人watermark参与。缓存命中仍检查禁用/撤销；tenant未进入近期范围不凭空加机构多租户承诺，但用户/目标隔离不可省略。

### 9.2 知识准备程序与代际

IndexBuildJob接收批准manifest→登记build_id/config/embedding profile→按内容修订分页→解析/切片/术语/向量→按(document_revision,chunk_locator,config_version)幂等upsert暂存代际→数量/引用/权限与黄金查询校验→ready→Java/索引控制面共同激活指针。未ready的代际不可用于新学习回答。

撤销先写当前deny集合并通知Java引用检查，索引删除/缓存清理异步；旧代际回滚也执行当前deny，不复活已撤销许可。Embedding重做费用也要预算/目的地授权；批处理中断按chunk checkpoint恢复，不重复嵌入已确定完成的内容。

### 9.3 行为特征算法

```text
extract(snapshot):
  if quality unavailable/conflicted: return limited features + limitations
  events = validate_option_membership_and_epoch(snapshot.events)
  deduplicate by event_id and stream/seq; conflicting same-key -> conflicted
  sort by seq; preserve gaps (do not invent missing events)
  maintain current_selection, first_selection, changed_count, cleared_count
  option_selected: if previous nonempty and different -> changed_count += 1
                   then update current_selection
  option_cleared: current_selection = empty; cleared_count += 1
  focus transitions: sum only valid foreground intervals with monotonic bounds
  final_answer = Submission.final_answer, never overwrite with event-derived last selection
  return features + quality/clock/sequence limitations
```

A→clear→C不计为直接改选次数，但保留候选变化/取消和完整序列，不能因此认定“没犹豫”；直接A→C计1。重复点同一选项不计改选；多选题按批准题型的集合变化策略，未批准前不要套单选规则。没有可靠展示/聚焦起点或时钟倒退时，foreground_ms=null并带限制；离线/后台不能一律算思考时长。

### 9.4 学习证据、画像与计划算法

EvidencePolicy先判断题型/版本/答案暴露/辅助/重复题族/独立性/当前目标，返回eligible＋reason，而不是LLM决定。LA-02线索只作支持/反证候选；Java批准策略计算画像，未批准mastery estimator时不生成数值概率，只展示练习事实/待验证。

个人知识link按(node,evidence_source,revision)唯一，撤销或新分析重评资格但保留历史。画像聚合按evidence_watermark CAS，在同事务保存ProfileRevision与outcome，规划只读此确认水位。学生自评另列，不变成客观掌握证据。

规划：已确认范围/必要先修→检测环→候选拓扑顺序→过滤适用资源→按当前薄弱/复习到期/学生偏好排序→Java约束分配时间。学生可用时间、多目标共享预算、资源用时不可违反；无可行解给gaps，不压缩成不真实计划。ReviewPolicy决定时间/轮次；未批准自适应策略时固定教研间隔，独立延时复测验证效果。

## 10. DA：迁移、SQL、事务和状态一致性

### 10.1 DDL与所有者

[001_agent_runtime.sql](ai-agent/programming/sql/001_agent_runtime.sql)创建Python执行表；[002_learning_coordination.sql](ai-agent/programming/sql/002_learning_coordination.sql)创建Java协调骨架。两者在不同Owner/账号下迁移，演示可在同PG不同schema，生产隔离按部署决定；不能把同实例理解为允许Python写Java表。

DDL不安装pgvector或LangGraph内部表，不定义完整公共知识、个人画像与金融账本；这些仍按上位字段/领域Owner实现，不能拿协调骨架代替完整平台数据模型。迁移脚本只供空白专用schema验证，不用于覆盖现有生产库；Flyway/Alembic迁移命名及权限由工程落地。

### 10.2 关键Repository查询

```sql
-- Native PostgreSQL SQL shown as a specification; bind :parameters via adapter.
SELECT id, public_ref, state_revision
FROM agent_runtime.agent_run
WHERE status = 'queued' AND next_attempt_at <= clock_timestamp()
ORDER BY created_at
FOR UPDATE SKIP LOCKED LIMIT :batch_size;

UPDATE agent_runtime.agent_run
SET status = :new_status, state_revision = state_revision + 1,
    updated_at = clock_timestamp()
WHERE public_ref = :run_ref AND state_revision = :expected_revision
  AND fencing_token = :expected_fence AND status = :allowed_from;
-- affected_rows != 1 -> conflict/lease lost, never assume success.
```

本地认领同时写dispatch租约/next_attempt_at，不用长期持有上述锁。Java提案事务锁execution_fence和目标当前修订，先校验再修改；所有SQL使用绑定参数，sort/表名不能由模型传入。

### 10.3 不变量与事务边界

| 操作 | 同一事务内 | 事务外 / 恢复 |
|---|---|---|
| 确认Bundle | 草案expected revision、scope/initial plan/bundle/激活指针/Outbox | LLM候选生成在外；冲突重确认 |
| 最终提交 | Submission唯一/Grade、快照边界、cycle四项pending、Outbox | 行为批次/模型在外；尾部不合法不能拦合法答案 |
| Python接收 | Inbox＋run＋dispatch＋必要幂等收据 | ack在提交后；Worker扫描持久dispatch |
| 调模型 | 本地持久logical_call_intent；Java平台唯一Invocation＋预算各自事务 | 外呼不是跨系统事务；unknown对账，不盲目重发 |
| 采纳个人/计划 | 当前租约/授权/输入版本、CAS领域状态、outcome历史、receipt/Outbox | Python回执超时重取同命令，不新增logical任务 |

四类outcome有唯一键和历史修订；恰好四项由SubmitAttempt用例同事务写入/集成断言保证，单行CHECK无法表达跨行基数。部分失败记录failed/pending，不把四项全改updated伪造成功。全量no_change也须四项理由齐全。

### 10.4 迁移、保留、删除与恢复

先expand加列/索引→后台回填→兼容双读/消费者→切换→观察后contract；大索引生产使用经评估的在线方式，不盲执行示例普通CREATE INDEX。CHECK/唯一约束/回填中断/旧消息兼容都要在真实PG验证。

幂等/Inbox去重保留覆盖最大消息与任务重放窗口，截断旧消息重放入口后才清理；日志/正文/行为/检查点/账务各自按政策保留。删除先禁新副作用，处理领域/对象/投影/缓存/AI状态，备份恢复先重放删除禁用账本，再核对外部调用。Schema中TTL字段不构成留存审批。

## 11. 配置、运行与交付实现

### 11.1 Settings与环境矩阵

Settings字段组：service_role、environment、http/management_port、java_api_urls、broker_dsn_ref、runtime_db_ref、policy/model/prompt/graph manifests、otel_endpoint、max_pool/concurrency、shutdown_seconds。Secrets只保存引用，Provider密钥不在普通WorkerSettings。

启动校验：env/prod必须有已批准manifest与精确锁定版本，mock_auth/mock_provider必须false；端点/出站和受众有效；角色工具清单一致；依赖连接不超过配额；阈值参数从pilot文件进入生产前必须有批准记录。只有未批准AI功能保持禁用/降级，不影响Java基础答题服务就绪。

| 环境 | 模型/数据/依赖 | 发布与授权 |
|---|---|---|
| local | 合成seed、MockProvider、容器依赖 | 本机测试身份，不复用生产密钥 |
| test | 固定fixture及集成容器 | CI短期身份，真实模型测试单独预算 |
| stage | 批准测试内容/模型、接近生产拓扑 | 完整鉴权/密钥/网络；质量/负载/恢复验收 |
| prod | 已批准用户/内容/目的地与策略 | 签名制品/受保护GitOps，真实监控与值班 |

### 11.2 启动、探针和退出

API /health/live查局部事件循环；/health/ready查接单能力、必要授权/存储可用；/health/startup初始化清单/连接完成。外部模型失败不作为liveness失败，避免全体重启。Worker设独立管理端口8081，SIGTERM后ready=false/停止claim，保存步骤与投递状态，有界等待/释放租约，Provider在途保持可查询/unknown。

Kubernetes部署模板沿上位附件补齐真实image digest、secret投射、工作负载身份交换、默认拒绝NetworkPolicy、CPU/内存/连接池/PDB/拓扑。Namespace不等于强隔离，Provider与抓取分身份/出网，普通Agent无KMS解密权限。迁移Job独立，Argo CD同步顺序明确不在每Pod启动建表。

### 11.3 CI/CD任务及质量门禁

CI执行契约/代码生成漂移→Ruff/mypy/Java格式/依赖边界→单元/性质→真实DB/消息/鉴权集成→固定AI质量集/安全对抗→迁移/恢复→镜像/SBOM/签名/漏洞/许可。平台中立任务接入团队选择的CI Runner，文档不假定已有GitHub/GitLab账户或远程仓库。

CD由Argo CD同步受保护环境声明，同一镜像摘要逐环境晋级；graph/prompt/policy/schema/index/ModelProfile分别版本化。灰度同时观测业务结果、隐私拒绝、费用与性能，不能只看HTTP200；若核心不变量破坏立即停止/回滚。旧run兼容Worker池保留到任务完成或显式迁移。

### 11.4 运行排障定位

request/cycle/event/run/step/tool/Invocation/proposal/receipt关联追踪；指标标签有限，全文默认不采。问题定位顺序：Java答案/四项事实→Outbox/Inbox→run/租约→step工具/模型→proposal收据→输入版本/策略。学生“画像没变”可能是no_change不是失败；未知费用不能因为run失败就释放账本。

告警、值班、灾备与删除恢复沿上位第11章；本篇补入SQL/lease/proposal排查入口。实际SLO和RPO/RTO需实测，模板部署成功不等于业务可生产。

## 12. 测试规格、可运行脚手架验收与开发任务

### 12.1 测试边界与组件样例

[component-cases.json](ai-agent/programming/component-cases.json)列出组件、场景、输入、预期、不变量、层次、角色及需求。它是测试开发输入，不是已经执行的业务测试。单元用FakePorts/固定clock/model；集成用真实PG/RabbitMQ和JWT验证；AI评测用冻结样本/版本且限定费用，不能把mock质量当真实教学质量。

必须覆盖：Strict DTO extra字段/类型、分页绑定/越权、context裁剪不丢限制、工具白名单、canonical幂等冲突、两端确认、同答案同分、行为乱序/缺失/迟到、分支失败不取消成功支路、租约过期、节点重跑、unknown费用、版本冲突/新范围、四项no_change、撤销/跨用户缓存、图升级、删除恢复。

AI质量按上位独立黄金集/教研门槛执行，新增Agent做消融对比；规则与程序测试不证明学习有效。确切样本/置信/阈值由T-04/12/21/25批准，不能凭少量示例给99%准确率。

### 12.2 脚手架完成定义

| 阶段 | 可执行验收 | 不能用来替代 |
|---|---|---|
| SC-0 工程构建 | 锁文件/BOM、代码生成、测试/容器构建均成功 | 只有目录或dependency范围 |
| SC-1 本地启动 | 各入口+健康检查+迁移+合成seed可重复启动 | 启动一个FastAPI返回200 |
| SC-2 最小业务链 | Java→消息→Python图/MockProvider→提案→Java结果→查询trace | Agent只打印文本 |
| SC-3 故障与安全 | 重复消息/Worker重启/非法权限/模型失败/旧fence均按预期 | 只正常路径smoke |
| SC-4 预发验证 | Kubernetes真实依赖、鉴权、网络、安全/质量/容量/恢复证据 | YAML解析/Schema通过 |

本轮只编写这些验收规格和模板；未来实际生成脚手架后逐项记录成功证据，G0～G4生产门禁继续有效。

### 12.3 按依赖拆分的开发任务

| 工作项 | 责任 / 依赖 | 完成条件 |
|---|---|---|
| DEV-01 锁定基线/脚手架 | 平台＋Java/Python；先行 | 兼容PoC、精确锁/镜像、SC-0/1；代码和文档一致 |
| DEV-02 契约/身份/配置 | Java/Python/安全；DEV-01 | DTO/验证器/生成清单、workload JWT、环境约束 |
| DEV-03 学习核心规则 | Java＋教研；DEV-02 | 草案确认/题目/提交评分/四项/租约/幂等Outbox真实事务 |
| DEV-04 Runtime/消息/恢复 | Python＋SRE；DEV-02/03 | Inbox/run/dispatch/checkpoint/fence/控制/重入故障验证 |
| DEV-05 Provider/预算 | Python＋Java平台；DEV-02/03 | 预留/begin/结果/settle/unknown，不重复逻辑调用 |
| DEV-06 RAG/证据 | 检索＋知识域；DEV-02，内容并行 | 授权查询/词项向量/代际/撤销/引用独立集 |
| DEV-07 LA-02/03 | AI＋教研；DEV-04/05/06 | 行为有限分析/有据讲解、角色与联合评测 |
| DEV-08 LA-05/04 | AI＋Java数据/教研；DEV-03/07 | 确认证据水位/个人建议/计划约束/复习策略批准 |
| DEV-09 LA-01/Assist与UI | AI/产品/前端；DEV-07/08，可早期Mock联调 | 复杂意图/澄清、首次共建与异步四项体验 |
| DEV-10 生产准备 | 安全/SRE/测试；上述逐步汇合 | SC-3/4、上位G0～G4、值班和灾备签证据 |

每项关联需求/AT/组件场景、实现PR或commit、镜像/配置版本和实际结果；团队人数/环境/许可未知，不虚构工期。

## 13. 设计关联、待决策与维护

### 13.1 上位到程序的追溯

| 上位详细设计 | 本篇实现落点 |
|---|---|
| 第2章业务/第4章五Agent | 第2、6～7章、component-cases |
| 第3章模块/第7章契约 | 第4～5、8章、scaffold-blueprint/ports |
| 第5章协作与恢复 | 第6章、DDL run/step/dispatch/lease、故障样例 |
| 第6章RAG | 第9章检索/准备/撤销算法及职责 |
| 第8章数据 | 第10章两份DDL/事务/迁移/保留 |
| 第9～11章安全/运行 | 第3、8、11章及SC验收 |
| 第12章验证/门禁 | 第12章DEV任务/SC验收与上位AT用例交叉关联 |

### 13.2 待决策和上线限制

已选框架方案/接口/算法骨架不再留给各开发自行决定。必须在对应门禁关闭：精确版本/兼容与许可证G0；资料/答案/许可和确认交互G1；教学证据/复习/质量/模型目的地/预算G2；行为授权/保留/地区/容量/网络/恢复G3。Policy未批准时禁用相应AI或采用明确规则基线，不阻断可独立实现的工程任务。

CI供应商/集群托管方由部署团队选择，任务接口和GitOps交付方式已明确；数据库投产权限、密钥服务与工作负载信任关系需真实环境配置。本轮未运行服务或宣称模板生产可用。

每次变更核对需求、架构、上位详细设计、本文及契约，运行适用检查并记录未验证项，再Git commit。历史归档不改，既有平台全量追溯待同步事项不因本篇存在而自动关闭。
