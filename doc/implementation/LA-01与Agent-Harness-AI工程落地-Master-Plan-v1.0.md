# LA-01与Agent Harness——AI工程落地 Master Plan v1.0

| 属性 | 内容 |
|---|---|
| 日期 / 状态 | 2026-10-19；可执行工程计划评审稿；已做计划级推演，尚未开始生成应用工程 |
| 目标 | 指导AI从零构建脚手架、Java业务应用、Python Harness/Agent、前端验证界面、测试、交付与运行证据，落实LA-01企业级设计 |
| 执行模式 | 依赖驱动、每次完成一个可验收工作包；可跨会话恢复；默认单执行者，不要求并行AI |
| 本次交付 | 仅新增本文；不生成应用、不修改原设计/契约、不触发外部模型付费或部署 |
| 任务状态 | 全部工程任务初始todo；第11章的计划推演不代表任务完成 |
| Git原则 | 每个已完成工作包独立commit；只提交任务内文件；未授权不push、不部署生产 |

## 1. 依据、范围与最终交付定义

### 1.1 AI必须读取的基线

- [LA-01需求与C4详细设计](../design/agents/LA-01-学习协调Agent-需求与C4详细设计-v1.0.md)：主实施规格；优先关注第17～20章、HR-01～12、HV-01～16。
- [通用Harness参考架构](../architecture/通用Agent-Harness-参考架构与工程规范-v1.0.md)：共享机制、恢复、安全与质量约束。
- [Agent群程序设计与脚手架](../design/学生持续学习-AI-Agent群程序设计与工程脚手架-v1.0.md)及[蓝图](../design/ai-agent/programming/scaffold-blueprint.json)：技术候选线、工程模块、端口和DDL模板。
- [Agent群详细设计](../design/学生持续学习-AI-Agent群详细设计-v1.0.md)、[需求v0.3](../requirements/通用Agentic学习与考试平台-系统需求规格说明书-v0.3.md)、[4A总体v1.1](../architecture/通用Agentic学习与考试平台-4A总体架构设计-v1.1.md)、[多Agent/RAG专项](../architecture/学生持续学习-多Agent与RAG-4A专项架构设计-v1.0.md)：业务事实、学习链、四项更新和整体边界。
- [LA-01 Schema](../design/agents/la-01/contracts/la01.schema.json)、[OpenAPI](../design/agents/la-01/contracts/la01.openapi.json)、[工作流目录](../design/agents/la-01/contracts/workflow-catalog.json)、[工程政策](../design/agents/la-01/contracts/agentic-policy.json)、[公共Schema](../design/ai-agent/contracts/learning-agent.schema.json)、[公共API](../design/ai-agent/contracts/learning-agent.openapi.json)：机器契约输入。

文档冲突必须在M00登记并在M02完成契约映射/ADR，不静默“择一实现”。LA-01局部IntentProposal/CoordinationPlan是完整协调协议，旧CoordinationOutput仅兼容投影；RunCreateRequest不接受plan_change。通用规范示例API不替代现有5条LA-01接口。蓝图roles旧输出定义需在契约映射中解释，不直接据其生成错误DTO。

### 1.2 此计划交付什么

交付LA-01及其依赖的完整纵向业务切片：学生选择范围、确认基础路线、取题作答和行为记录→Java保存结果→自然语言讲解/重排/联合请求→LA-01受控路由→LA-02分析、LA-03讲解、LA-05个人证据、Java确认水位、LA-04规划→学习/复习计划与个人知识/画像的正式收据→页面可见、确认、复习、取消和恢复。

Java负责身份、题目/答案/知识版本、目标、答题事实、正式更新、权限、预算、收据；Python负责Harness、模型/RAG/Agent和固定编排。首次图谱和基础路线可由Java规则生成，明确页面动作不经LA-01。评分以Java权威答案/规则为准，Agent不投票改分。

范围包括最小可信知识导入/审核/发布、图谱节点/关系与题目映射；不扩为全平台商业化、收费退款、全学科内容运营、互联网自动采集或基础模型训练。正式上线所需权威题材必须经授权/学科审查，合成题只证明工程闭环。

WEB提供可实际操作的响应式学生验证界面；APP复用鉴权/API、对象权限和恢复语义，并完成移动视口/客户端契约测试。本期不声称交付原生iOS/Android安装包；若后续要求安装包，必须新增客户端发布任务并调整最终范围，不能以移动网页冒充原生APP完成。

### 1.3 三种完成层级

| 层级 | 终点 | 必须满足 | 不可推导 |
|---|---|---|---|
| L1 本地工程闭环 | M30 | 干净克隆按锁文件启动；真实DB/消息/Java/Python/WEB，固定MockProvider无外部费用，三模板与故障场景通过 | 不代表真实模型理解正确或题库权威 |
| L2 真实模型与预发闭环 | M33 | 真实模型/批准语料评测，预发环境真实链路、隔离/性能/恢复/删除/回滚通过 | 不代表已获生产发布授权 |
| L3 生产验收闭环 | M35 | 发布包、授权、生产晋级、观测期、业务/SRE/安全签认齐备 | 没有环境/批准/真实证据不得称完成 |

总目标为L3；L1/L2是可独立验收里程碑。缺少外部资源时可完成不依赖它的任务，最终报告必须写“L1完成、L2/L3阻塞于具体事项”，不能把任务改成skip来伪造闭环。

## 2. AI执行协议：怎样按计划工作

### 2.1 每次会话的固定动作

1. 确认仓库根、分支、git status、适用AGENTS.md与现有任务账本；保留用户已存在的修改。当前基线有一处Agent群详细设计的未提交用户改动，以及无关workspace目录，均不属于本计划可覆盖范围。
2. 读取本文、execution/task-state.json与上次交接；对所选任务重新读取对应设计章节，核对契约hash和依赖证据。
3. 选一个依赖已done的todo/failed任务；若外部条件未满足，登记awaiting_external并选择其他ready任务。不要先编码后找设计。
4. 建立任务输入清单、允许改动路径和验收用例；实现最小完整切片，调用真实依赖测试相应边界。
5. 运行任务命令及受影响回归，保存退出码、命令、工具/环境版本、脱敏日志、测试摘要与产物hash。失败先修复，不能降低断言或把真实依赖换Mock后沿用原验收名称。
6. 复核需求/安全/状态不变量、diff、密钥扫描；只stage本任务文件，更新任务证据/交接并commit。
7. 输出完成内容、证据、剩余风险和下一个ready任务；未完成任务保持进行中/失败/外部阻塞，不凭代码量判done。

若某工作包超过一个上下文窗口，拆为带父ID的小任务，保留原验收与依赖，不能把半成品工作包标done。继承已授权范围继续工作；生产发布、收费资源、用户数据等按现有授权处理，不假定“执行计划”自动授予所有外部权限。

### 2.2 状态、证据与交接

状态：todo→in_progress→verifying→done；失败为failed；缺资源/批准为awaiting_external。可选任务仅在对应能力明确disabled且有配置/负例证据时not_applicable。核心M00～M35不得not_applicable。任一done依赖失效或基线发生相关变更，任务转needs_revalidation并由影响分析决定回归范围。

M00创建账本，至少保存task_id、state、dependency_evidence、baseline_refs/hashes、allowed_paths、commands/exit_codes、artifact_refs/hashes、test_results、unresolved、commit_ref与next_action。账本不是安全授权来源，发布Gate必须读取实际产物/测试和签认。

执行证据计划放execution/evidence/{task_id}/{attempt_id}/；日志必须脱敏，不提交Key、Cookie、真实学生正文、数据库备份或包含秘密的环境文件。每个任务保存review.md与result.json；交接放execution/handoff.md。commit_ref可用提交后追加账本记录或独立git note记录，不制造“本提交文件必须包含本提交SHA”的循环。

### 2.3 停止与升级条件

- 设计/契约冲突阻断当前任务：写issue/ADR、列影响和建议；不能自行扩枚举或隐藏新增权限。
- 工具/基础库兼容失败：保存PoC证据，调整同一兼容组合；不能为了启动删除鉴权、检查点或事务。
- 实现测试持续失败：按根因修复；需外部条件则明确阻塞；禁止空测试、pytest未收集也报成功。
- 未知副作用：停止该写操作重试，查询/对账；不直接SQL修改成功状态。
- 发现泄密/越权：停止相关能力、撤销测试凭据、记录最小证据；修复与复测前不晋级。

## 3. 目标工程结构与技术锁定

### 3.1 计划目录

以下路径均为未来任务产物，不表示当前仓库已有实现。不得复用无关workspace应用来充当本工程。

```text
contracts/                              # 源映射、版本、生成器、JSON Schema/OpenAPI/事件
services/java/
  pom.xml / mvnw / .mvn/               # 受锁BOM、Enforcer与模块
  learning-core/                      # 目标/答题/四项/Assist/收据
  knowledge-service/                  # 已审内容/图谱/题目版本
  platform-service/                   # 身份代理/权限/预算/Invocation/租约
  gateway-bff/                        # 学生接入、会话与查询；不强制SSE
services/python/
  learning-agent/                     # src/learning_agent/{domain,ports,agents,...}
    pyproject.toml / uv.lock / migrations/ / tests/
  provider/                           # 独立密钥/厂商SDK/出网边界
apps/student-web/                     # 响应式WEB与移动视口验证
infra/local/                          # compose、测试身份与合成内容
infra/k8s/{base,overlays}/             # test/stage/prod，默认不自动部署prod
pipelines/                            # CI任务、签名、晋级与门禁
scripts/                              # 工具核验、生成、验证、演练
execution/                            # task-state、handoff、脱敏证据、release manifest
Makefile / .env.example               # 无秘密、命令稳定、失败非零退出
```

Java初期四模块与明确领域边界，不为每个实体拆微服务；Python Agent不得导入数据库/HTTP/提供者SDK，使用自有Port。Provider独立进程/镜像，普通Worker不能解密Key。框架Checkpoint与业务操作台账职责分别实现。

### 3.2 技术决策任务，而非盲目固定版本

既有设计的JDK21、Spring Boot/Cloud/Alibaba组合、Python维护线、LangGraph及数据库驱动为M01候选输入。M01必须查询官方支持/兼容矩阵并完成本机或容器PoC，输出具体patch、BOM、uv.lock、镜像digest、支持窗口、安全与许可证证据。不能默认历史文档中的范围仍兼容，也不得所有包取latest。

前端参考React＋TypeScript＋可维护构建工具，Playwright做E2E；M01核验兼容/安全并锁定。若团队另有已批准技术栈，记录ADR再替换，产品状态和契约不变。Spring Cloud Alibaba按确有需求启用注册/配置等组件；不因产品名就引入分布式事务或自动全量治理套件。

基础设施沿PostgreSQL/pgvector、RabbitMQ、Valkey、S3兼容存储、OTel方向；锁版本、ARM/x86镜像与原生依赖分别验证。缓存不得承担业务/预算账本。开发身份使用真实签名/验证的隔离OIDC测试域；生产不得使用开发签名密钥或认证旁路。

## 4. 命令契约与任务完成判定

M03～M04负责创建下列命令；创建前不得宣称命令已可用。Make只是统一入口，底层必须执行实际构建/测试/部署脚本。

| 命令 | 行为与成功条件 |
|---|---|
| make doctor | 检查JDK/Python/uv/Node/容器/端口/资源，明确缺项，不输出秘密 |
| make bootstrap | frozen锁文件安装；无锁进入M01，不自动升级 |
| make contracts | 校验原/新Schema与兼容映射，生成双端DTO、漂移检测 |
| make dev-up / dev-down | 健康就绪的本地基础服务；down不默认删除持久数据 |
| make migrate / seed-demo | 显式有序迁移；仅开发环境幂等合成种子，禁止误写生产 |
| make app-up / app-down | 启动/停止Java、Python API/Worker/RAG/Provider与WEB，失败可诊断 |
| make test-unit / test-contract / test-integration | 分层测试；缺必要依赖明确失败/blocked，不静默跳过 |
| make verify TASK=Mxx | 分派到该任务真实验证脚本，要求存在测试与非零断言数；未实现任务非零退出 |
| make smoke-learning / smoke-assist | 完整学习循环/三类协调模板及真实收据验证 |
| make fault-redelivery / test-recovery | 重投、fence、提交后崩溃、unknown、取消/灾备场景 |
| make test-e2e / test-security / test-load | 浏览器与APP契约、安全负例、独立负载配置 |
| make eval-real | 需批准模型/语料/预算；报告真实模型/参数/数据与费用，缺条件不能pass |
| make package / deploy-stage | 构建签名镜像/SBOM；向批准预发环境部署，不隐式触及生产 |
| make plan-check / gate-local / gate-stage / gate-release | 检查依赖/证据/产物与门禁，未满足条件非零退出 |

每个任务卡的“验证”默认先make verify TASK=ID，再执行所列专项命令。M00～M03命令入口未齐时用等价原生命令，并把命令固化至M04脚本。禁止verify只检查文件存在、只执行文档检查器或以TODO/NotImplementedError冒充业务实现。M04只建立已实现任务的验证入口，未实现任务明确失败，测试随后续任务持续加入，不要求提前伪造全套通过报告。

## 5. 阶段与执行任务卡

卡片中的“依赖”以第6章JSON为唯一机器基准；改任务必须同时改JSON、卡片和覆盖映射。任务ID不是时间估算，执行顺序由依赖决定。每卡继承第2章证据/commit要求，所列paths是工作范围，不允许覆盖无关用户文件。

### 阶段A：基线、契约与可启动工程

#### M00 基线审计、范围与执行账本

- 依据：本文第1～2章、LA-01第17/20章；无前置任务。
- 执行：读取全部基线与git状态；登记冲突/现有待批准T项、功能禁用项、外部依赖；创建task-state/evidence/handoff与计划依赖检查器雏形。
- 产物：execution/baseline-manifest.json、scope.md、task-state.json、coverage.json、external-dependencies.md；保存输入hash与原用户修改摘要。
- 验证：所有任务状态初始todo；范围明确L1/L2/L3，HR/AT/HV有负责人/任务；未改用户内容。读取基线有歧义先记录，M02前不得生成冲突DTO。

#### M01 工具链、版本与兼容PoC

- 执行：核验现有运行环境；查官方支持矩阵；锁Java/Python/前端/基础设施/SDK组合；以隔离临时PoC验证启动、数据库/消息/原生扩展、LangGraph持久化与供应商SDK能力。
- 产物：execution/technology-lock-manifest.json、兼容ADR、PoC源码/结果、工具安装/缺失清单；有批准再使用外部付费资源。
- 验证：受支持版本/镜像digest可解析，Java BOM收敛、Python wheel可用、主开发平台可构建；真模型调用质量留M31，PoC可离线MockSDK协议。

#### M02 契约归一、缺口补齐与生成映射

- 执行：导入原公共/LA-01契约与目录hash；补充设计中未落机器契约的内部Profile、execution_control、事件、委派账本、审批/预算/结果引用及领域最小接口；分清已有与新版本。
- 产物：contracts/源清单、兼容矩阵、Schema/OpenAPI、DTO生成配置/黄金样例；新增字段走版本/适配，不原地破坏原闭合结构。
- 验证：Java/Python对同一正/负例结论一致；5意图/3模板、plan_change兼容投影、状态映射、水位依赖均可表达；所有缺口有明确协议，无“开发时再猜”。

#### M03 生成可构建脚手架

- 执行：按第3章生成Maven模块、Python src包/独立Provider、WEB、依赖锁、环境模板、Dockerfile、健康接口、构造/Composition Root与测试目录；配置.gitignore排除秘密/运行数据，引入M02 DTO生成。
- 产物：services/、apps/、contracts/生成清单、根命令入口；业务空壳标明尚未实现，不宣称完成。
- 验证：原生Maven compile/test、uv frozen sync/导入、前端类型检查与构建、空服务健康启动；无导入即联网/迁移/密钥读取。

#### M04 统一构建、CI和任务证据检查

- 执行：实现第4章命令入口、分层测试目录、plan-check/verify路由、质量与秘密扫描、失败非零退出；CI从干净克隆按锁安装。
- 产物：Makefile、scripts/、pipelines/基础任务、证据Schema/校验器；未实现命令明确失败。
- 验证：故意引入坏Schema/缺测试/伪done/泄密样例均阻断，恢复后基础构建通过；不能把无测试报告视为通过。

#### M05 本地真实依赖与身份环境

- 执行：Compose启动PG/扩展、RabbitMQ、缓存、对象存储、OTel与隔离OIDC；本机绑定、健康探针、资源限额及开发/生产隔离。
- 产物：infra/local、.env.example、环境校验与清理脚本；本地凭据按测试策略生成、不入仓库。
- 验证：make dev-up/doctor，连接/重启/就绪检查；无法连接必须明确失败；安全默认值阻止误用prod。

#### M06 执行库与业务库迁移

- 执行：审查既有DDL模板，补齐最小领域表、租户复合键、唯一键、事件/Inbox/Outbox、调用台账、审批、预算、删除墓碑；Flyway/Alembic/框架Checkpoint迁移分工。
- 产物：两端迁移、Schema权限与索引、向前/兼容迁移方案。
- 验证：真实PG新库迁移/重复运行、约束冲突/并发CAS、旧版本升级、备份恢复样本；Pod启动不自行抢迁移。

### 阶段B：Java业务地基与Python执行地基

#### M07 认证授权与租户/目的隔离

- 执行：Java学生Cookie/APP Bearer与内部workload身份分链，CSRF/issuer/audience/scope、对象归属/目的检查；Python验证调用身份与任务绑定；无默认放行。
- 产物：两端安全适配、PolicyPort、测试用户/跨租户场景。
- 验证：真实签名Token、错误受众、过期、跨用户/目标/内部接口与CSRF负例，审计无秘密；make test-security基础集。

#### M08 最小知识母本、图谱与题库

- 执行：实现学科/节点/先修/题目/权威答案/来源许可/年度/版本、草稿→审核→发布及失效；创建合成示例与导入CLI/API，不为所有学科设计后台。
- 产物：knowledge-service领域逻辑、合成数据、审核/发布命令、版本查询与权限接口。
- 验证：未审内容不出题；引用可追溯；发布版本不可被原地改写；失效/无许可/无题明确缺口；seed-demo可幂等运行。

#### M09 Java学习主链与行为证据

- 执行：选范围→Java基础图谱/路线草案→编辑确认Bundle→逐题/最终答案→评分/Submission→行为轨迹关联；学习/复习任务与恢复接口；提交同事务写Outbox和四项pending，之后触发attempt工作流，不要求学生先聊天。
- 产物：learning-core领域、公开API、最小用户/目标/计划/个人资产模型与fixture；行为缺失不阻断最终答案保存。
- 验证：不经LA-01完成页面确定动作；答案A→C等轨迹与最终答案分离；已提交不重复评分；复习只基于合法历史；并发版本冲突。

#### M10 Java预算、Invocation、租约与密钥代理协议

- 执行：原子预占/子分配/结算/unknown对账，Invocation开始/查询，run-leases与fence；Provider所需密钥引用及授权/目的地策略，提供用户AI配置/加密保存/替换/撤销接口与Key所有权校验。
- 产物：platform-service预算/Invocation/lease实现，API与价格版本记录；不将密钥给Worker。
- 验证：并发子分配不超总额、同操作幂等、unknown非0、旧fence无效、撤销即时阻断；使用真实PG事务。

#### M11 Java Assist入口与可信Context

- 执行：实现现有5条LA-01 API；持久接收/幂等/Outbox、查询/取消/澄清、候选目标/能力、最小Context和结果引用授权；未选目标不填虚构InputRefs。
- 产物：AssistRequestService、上下文/问题存储、API契约测试与异步投递。
- 验证：同键异内容409、过期/旧回答冲突、学生不能填auth或控制他人run；接收不等待模型、Java页面路径仍独立。

#### M12 Python持久Runtime与消息控制

- 执行：实现API/Worker/RunController、固定release/graph、Inbox/Outbox、lease/fence、Checkpoint与execution_control、状态CAS、恢复扫描和幂等接收。
- 产物：自有RuntimePort/LangGraph Adapter、Repository、AMQP适配、恢复入口；真实PG/消息测试。
- 验证：Worker重启可恢复、同消息10次一个逻辑Step、旧Worker拒写、等待不占Worker槽位；不重放外部副作用。

#### M13 Harness内核Hook、动作闸门与停止规则

- 执行：实现HR-01完整顺序、宿主授权命令DTO、before_model/action、预算/取消/截止、结果校验/Finalizer机制、清理与无进展检测。
- 产物：Harness application/policies、Hook注册/不可绕过边界、Port测试。
- 验证：恶意中间件/模型不能直接执行工具/写终态；费用/步骤/时间有界；旧权限与取消版本不复用；HV-01/02确定性部分。

#### M14 上下文、记忆与Profile装配

- 执行：实现计数适配、4096/600/256试点与更小上限、保护片段/Manifest、记忆作用域/有效期/摘要来源；禁同步LLM压缩、关闭脚本/动态委派。
- 产物：ContextAssembler/MemoryPort/RoleResolver及Profile Schema/配置与计数测试。
- 验证：工具/Schema/Skill计入总量，否定/未完成诉求保留、超窗澄清；跨目标/撤销/墓碑阻断；真实Tokenizer对照留M31复核。

#### M15 Provider：Fake与真实SDK适配

- 执行：独立Provider进程、ModelPort、结构化输出/超时/流能力配置、调用查询/用量/unknown、批准回退；实现固定FakeProvider以本地可复现；用户自配AI按当前Key/目的地/模型能力解析，撤销后新调用立即阻断。
- 产物：Provider包/镜像、秘密代理、真实供应商适配及合约测试；默认fake模式显式标记。
- 验证：Worker无Key/SDK权限，目的地白名单、预算引用、请求已发送超时的unknown、有限修复与回退；真实模型付费执行留M31。

### 阶段C：LA-01、领域提交与四类叶Agent

#### M16 LA-01规则、Prompt和意图校验

- 执行：IntentRouter、注册精确规则、受限Prompt和IntentProposal校验；正常1调用、最多1修复且共用3s；保留多意图/否定，缺对象澄清。
- 产物：agents/la01_router、Prompt版本与决策用例；自然语言黄金集草案。
- 验证：Fake合约覆盖5种意图、模糊/越权/非法字段；模型正确理解的结论必须等M31，不能靠Fake答对算准确率。

#### M17 决策Gate与固定模板编译

- 执行：重读当前Context、权限/范围/证据/能力/修订检查，3模板精确编译、step绑定、兼容输出投影；决策/Plan/dispatch意图同事务。
- 产物：DecisionPolicyGate/Compiler、Plan持久化与模板版本校验。
- 验证：拒绝任意DAG/Agent/未知scope、旧输出和缺证据；联合模板commit_personal依赖不变；与现行公共Run协议兼容。

#### M18 Java提案采纳、四项更新与业务收据

- 执行：实现Proposal接收/校验、操作唯一键/expected_revision、个人知识/画像、学习计划/复习计划更新与no_change/拒绝/候选收据；计划激活需必要确认。
- 产物：领域命令/事务与receipt查询；个人确认水位可供下游读取。
- 验证：同提案10次一次生效、冲突/迟到数据不覆盖、四项状态独立可见；候选已保存不等于已激活；标准分数不可被Agent改写。

#### M19 RAG与证据服务

- 执行：授权范围解析、关键词/向量候选与必要重排、版本/有效期/许可/冲突过滤、EvidenceBundle、出处/引用验证；对中文与学科术语建立检索集。
- 产物：rag-api/EvidencePort、索引/导入、合成证据集和检索评测；LA-01不默认调用。
- 验证：未审/跨租户/过期内容不返回，无证据明确不足；引用存在和支持结论分别测；真实权威资料质量留M31。

#### M20 LA-02作答与行为分析

- 执行：已提交结果/轨迹→观察与推断分离→AnalysisOutput，引用证据/限制；缺行为可降级，不重判权威分数。
- 产物：AttemptAnalysisAgent、特征提取/规则与按需模型、Schema/证据测试。
- 验证：A→C不自动定性不掌握；推断有来源/置信限制；重投不新增同一证据；真实模型质量待M31。

#### M21 LA-03有依据的讲解

- 执行：按批准题目/分析和EvidenceBundle生成讲解/引用/不足，保存Artifact候选，经Java采纳；冲突转复核。
- 产物：TutorAgent、ExplanationOutput、事实/引用/安全校验。
- 验证：Fake可测试流程但不证明教学质量；无证据/错年度不伪造权威；讲解保存有收据且不改分。

#### M22 LA-05个人知识与画像建议

- 执行：分析证据→个人知识/画像候选，区分确认/推断/争议；提交Java提案后取confirmed watermark。
- 产物：PersonalEvidenceAgent、PersonalOutput、采纳适配与幂等证据引用。
- 验证：不直接写权威表、不升格公共母本；重复/冲突/旧版本无污染；成功以Java收据/水位为准。

#### M23 LA-04学习与复习规划

- 执行：基于确认水位、目标/先修/剩余时间/可用证据生成PlanOutput、学习/复习建议；无法满足约束明确解释/澄清。
- 产物：LearningPlannerAgent、约束校验/规则基线、候选保存/激活适配。
- 验证：先修/时间/范围不突破；联合模板不使用假新画像；无历史不称为复习；规则基础路线无需强制LLM。

#### M24 固定多Agent协作与结果聚合

- 执行：Dispatcher按3模板创建去重叶任务/DAG，Handoff核验、深度1/最多2并行、原子子预算/取消传播、Java水位依赖、ResultAssembler与Finalizer。
- 产物：assist/attempt工作流、类型化子任务结果/账本、收据聚合与公开投影适配；答题提交Outbox自动进入attempt，复习提交复用该链路，不强制经过LA-01。
- 验证：explain/replan/联合请求全走真实服务与持久化；讲解失败不回滚个人事实；缺必需目标partial；业务unknown不提前终态。

### 阶段D：交互、可恢复性与产品闭环

#### M25 澄清、取消、unknown与恢复对账

- 执行：结束routing后持久问题/新关联run，15分钟/2轮试点；内部核对映射公开executing/cancelling；操作查询/退避/人工处理、父子取消。
- 产物：恢复/对账器、到期扫描、人工核对操作入口与审计、取消结果投影。
- 验证：过期/两端回答一次消费、提交和取消竞争、无幂等第三方不盲重试；HV-03～09核心故障集。

#### M26 WEB/移动交互与完整学习旅程

- 执行：开发登录/选范围/确认路线/逐题/行为/提交/结果/自然语言/澄清/计划确认/复习/状态查询与重连，以及平台AI/用户自配AI设置、用途/费用提示与Key撤销；可访问键盘/状态提示与API客户端安全。
- 产物：student-web、移动视口和APP客户端契约测试；不新增未批SSE，不展示隐藏推理。
- 验证：Playwright真实服务E2E、两端并发、断网乱序/取消/partial/候选待确认；页面命令LA-01模型数0；原生APP不冒充完成。

#### M27 Trace、审计、指标和反馈

- 执行：跨服务/消息因果、请求到业务收据/学生结果、脱敏/审计不可采样、unknown/队列/成本仪表盘、反馈样本与离线回放。
- 产物：OTel Collector配置、仪表盘/告警、政策Span allowlist版本映射和回放工具。
- 验证：同请求可定位所有关键环节，日志/产物不泄密；审计失败关闭高风险动作；回放不真实扣费/写业务。

#### M28 安全加固、删除与保留

- 执行：提示注入/跨租户/SSRF/工具漂移/批准重放/Key泄漏防护，Artifact下载、墓碑/缓存/索引/检查点/备份删除重放与行为数据保留。
- 产物：威胁模型、数据清单、自动安全测试、删除作业/扫描/证据；MCP/脚本禁用负例。
- 验证：关键安全负例全拒绝，删除后新读取立即受限；恢复不复活权限/数据；保留例外与负责人记录。

#### M29 全链路、故障与质量门禁自动化

- 执行：把28项AT、16项HV、24FR/23NFR和HR规则转为可执行测试及追踪矩阵；真实PG/消息/多进程故障注入、资源隔离与负载工具。
- 产物：测试套件/断言清单/覆盖矩阵/故障控制点、gate-local/stage/release实现；模型质量与生产环境证据分层。
- 验证：make test-unit test-contract test-integration test-e2e test-security test-recovery；故意失败/缺报告/旧证据必须阻断；未运行的M31/M33指标保持pending。

#### M30 干净环境复现与L1交付

- 执行：在干净克隆/独立环境按doctor→bootstrap→dev-up→migrate→seed-demo→app-up执行，运行3模板/作答/四项/复习/重连/故障测试，保存可复现说明与录屏/脱敏截图。
- 产物：L1 release manifest、锁文件/镜像、真实依赖测试证据、操作手册/演示数据、known-gaps。
- 验证：make gate-local、smoke-learning、smoke-assist全部通过；必须标FakeProvider/合成内容；Mock不是生产；停止应用再恢复可继续任务。

### 阶段E：真实质量、预发与生产交付

#### M31 真实模型、权威内容与专家评测

- 外部条件：批准的模型/Key/预算/目的地、合法语料/题库、学科与产品质量阈值/专家标注；缺项为awaiting_external。
- 执行：建立独立黄金/对抗/长上下文/学科检索集，真实计数、意图/复合请求/引用支持/教学质量/规划约束与费用时延评测；与规则基线/Fake分开报告。
- 产物：模型能力/价格/Profile锁、授权内容清单、样本与阈值版本、实际评测/费用和批准结论。
- 验证：make eval-real，关键安全零容忍；效果/费用满足批准门槛，未通过修代码/策略并回归相关M任务，不能放宽阈值凑pass。

#### M32 CI/CD、镜像与预发环境

- 外部条件：受信CI Runner、镜像仓库/签名、批准的预发K8s/域名/TLS/身份/密钥服务和数据依赖；本地kind可先测清单但不替代预发。
- 执行：OCI构建/SBOM/签名扫描、Kustomize、服务身份/网络/资源/出口、显式迁移Job、GitOps晋级与回滚；接入发布版本/存活就绪/优雅退出。
- 产物：infra/k8s、pipelines、镜像digest、部署/回滚脚本、预发Runbook；prod清单默认不自动apply。
- 验证：make package/deploy-stage；预发真实鉴权/依赖就绪，镜像/配置不可漂移，开发凭证无法用于预发。

#### M33 预发E2E、容量、灾备与L2验收

- 执行：在预发真实模型/批准内容执行旅程、10次重投/提交后崩溃/旧fence、取消/unknown/删除/回滚/备份恢复、WEB移动契约；测设计时延/队列/并发/费用及模型隔离。
- 产物：gate-stage报告、真实环境负载/恢复数据、RPO/RTO、容量预算、问题关闭与专家/UI/SRE/安全签认。
- 验证：M31质量批准、M32真实环境与全部关键不变量均满足；不允许用本地报告填预发字段；无证据不得L2。

#### M34 生产就绪发布包与批准请求

- 执行：汇总需求/测试/风险/镜像/模型/内容/Profile/协议/迁移/回滚/容量/值班/删除证据；核对可选能力禁用；生成变更与回退方案，识别未关风险。
- 产物：execution/release-candidate/manifest、release-review、验收清单与具体部署变更；用于申请有明确对象的最终生产授权。
- 验证：make gate-release要求所有必需证据及签认；批准尚未获得时发布包可就绪但生产批准标pending，不能把准备完成当可自动上线。

#### M35 生产灰度、观测与L3最终交接

- 外部条件：对M34具体发布包的明确生产授权、生产资源/凭据、值班安排、批准的灰度流量/观测窗口和业务验收负责人。
- 执行：受保护流程迁移/部署、小流量验证、监控目标完成/误执行/unknown/费用、安全/回滚止损；完成约定观测期后扩大或回退。
- 产物：实际部署记录、版本/收据/观测报告、业务/SRE/安全验收、运行手册/告警责任、L3 handover；不包含秘密。
- 验证：仅当生产实际证据与签认全部成立才done；部署失败/回滚即未完成，修复并重新评估。观察窗口未结束不得提前done。

### 可选工作包：显式禁用也是需要证明的配置

#### O01 MCP工具适配

- 默认not_applicable的条件：release明确production_enabled=false，模型目录无MCP工具，越权启用测试拒绝；核心任务不依赖它。
- 若批准启用：按LA-01第14章锁协议/SDK/端点/工具Schema，补认证、恶意结果/漂移/unknown/对象权限与Direct等价测试；更新政策/目录/契约/证据并重跑受影响M29/M31/M33/M34。
- 验证：启用但没有O01完成证据时gate-stage/release拒绝，不允许仍按默认禁用跳过。

#### O02 Skills加载与供应链

- 默认not_applicable的条件：Profile禁用动态包加载，固定Prompt可运行；脚本始终关闭；无包能力仍满足3模板。
- 若批准启用：实现注册/审核/哈希或签名/路径/许可/权限交集/预算/撤销，最多3个试点包，补消融/安全评测并重跑相关门禁。
- 验证：未知/撤销包拒绝；只有SKILL.md文件不算完成；若启用却未验证，阻断发布。

## 6. 机器可读任务图与需求追踪

本节JSON为任务依赖与覆盖的唯一机器源。M00提取到任务账本，M04实现plan-check自动校验；原文hash与提取版本一并保存。任务状态在账本更新，本文initial_state保留计划初始值，不随实施伪改为全部done。

FR/NFR/AT/HR/HV键为LA-01编号后缀；覆盖映射表示“负责实现/验证”，不是通过证明。可选MCP/Skills的需求在disabled模式由M28证明拒绝/未暴露；启用时必须完成O01/O02，且重新验证M33及其后续证据。不得以not_applicable免除已启用能力。

```json
{
  "plan_version": "1.0",
  "status": "planning_only",
  "tasks": [
    {"id": "M00", "depends_on": [], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M01", "depends_on": ["M00"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M02", "depends_on": ["M00", "M01"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M03", "depends_on": ["M01", "M02"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M04", "depends_on": ["M03"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M05", "depends_on": ["M01", "M03"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M06", "depends_on": ["M02", "M05"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M07", "depends_on": ["M03", "M06"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M08", "depends_on": ["M07"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M09", "depends_on": ["M08"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M10", "depends_on": ["M07"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M11", "depends_on": ["M09", "M10"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M12", "depends_on": ["M06", "M07", "M10"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M13", "depends_on": ["M10", "M12"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M14", "depends_on": ["M11", "M13"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M15", "depends_on": ["M10", "M13", "M14"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M16", "depends_on": ["M14", "M15"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M17", "depends_on": ["M11", "M16"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M18", "depends_on": ["M02", "M09", "M10"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M19", "depends_on": ["M08", "M12"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M20", "depends_on": ["M09", "M15"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M21", "depends_on": ["M15", "M18", "M19"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M22", "depends_on": ["M18", "M20"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M23", "depends_on": ["M09", "M15", "M18"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M24", "depends_on": ["M17", "M18", "M20", "M21", "M22", "M23"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M25", "depends_on": ["M11", "M24"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M26", "depends_on": ["M09", "M25"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M27", "depends_on": ["M11", "M15", "M24"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M28", "depends_on": ["M14", "M19", "M26", "M27"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M29", "depends_on": ["M04", "M25", "M28"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M30", "depends_on": ["M29"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M31", "depends_on": ["M30"], "initial_state": "todo", "optional": false, "external_conditions": ["approved_model_credentials_budget", "licensed_content_and_expert_thresholds"]},
    {"id": "M32", "depends_on": ["M30"], "initial_state": "todo", "optional": false, "external_conditions": ["approved_stage_infrastructure_and_ci"]},
    {"id": "M33", "depends_on": ["M31", "M32"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M34", "depends_on": ["M33"], "initial_state": "todo", "optional": false, "external_conditions": []},
    {"id": "M35", "depends_on": ["M34"], "initial_state": "todo", "optional": false, "external_conditions": ["authorized_production_release", "production_resources_and_observation_signoff"]},
    {"id": "O01", "depends_on": ["M07", "M15", "M19", "M30"], "initial_state": "todo", "optional": true, "external_conditions": []},
    {"id": "O02", "depends_on": ["M14", "M27", "M30"], "initial_state": "todo", "optional": true, "external_conditions": []}
  ],
  "milestones": {"L1": "M30", "L2": "M33", "L3": "M35"},
  "conditional_gate_dependencies": {"mcp_enabled": {"gate_task": "M33", "requires": ["O01"]}, "skills_enabled": {"gate_task": "M33", "requires": ["O02"]}},
  "coverage": {
    "FR": {
      "01": ["M07", "M11"],
      "02": ["M09", "M16", "M26"],
      "03": ["M11", "M14"],
      "04": ["M16", "M31"],
      "05": ["M11", "M25", "M26"],
      "06": ["M13", "M17"],
      "07": ["M07", "M10", "M17"],
      "08": ["M17", "M24"],
      "09": ["M24"],
      "10": ["M18", "M24", "M26"],
      "11": ["M06", "M12", "M18", "M25"],
      "12": ["M25"],
      "13": ["M15", "M16", "M26"],
      "14": ["M27", "M32"],
      "15": ["M08", "M21", "M26"],
      "16": ["M11", "M18", "M25"],
      "17": ["M24", "M29", "M31"],
      "18": ["M14", "M31"],
      "19": ["M14", "M28"],
      "20": ["M24"],
      "21": ["M27", "M29"],
      "22": ["M28", "O01"],
      "23": ["M28", "O01"],
      "24": ["M28", "O02"]
    },
    "NFR": {
      "01": ["M11", "M33"],
      "02": ["M13", "M16", "M33"],
      "03": ["M29", "M33"],
      "04": ["M26", "M33"],
      "05": ["M17", "M29", "M31"],
      "06": ["M12", "M18", "M25", "M29"],
      "07": ["M07", "M28"],
      "08": ["M14", "M28"],
      "09": ["M10", "M15", "M24"],
      "10": ["M27"],
      "11": ["M02", "M03", "M17"],
      "12": ["M25", "M33"],
      "13": ["M26", "M33"],
      "14": ["M01", "M04", "M32"],
      "15": ["M11", "M17", "M25"],
      "16": ["M14", "M31"],
      "17": ["M14", "M28"],
      "18": ["M24", "M25", "M29"],
      "19": ["M13", "M19", "M28"],
      "20": ["M28", "O01"],
      "21": ["M28", "O02"],
      "22": ["M27", "M28"],
      "23": ["M29", "M31", "M35"]
    },
    "AT": {
      "01": ["M11", "M21", "M26"],
      "02": ["M09", "M16", "M26"],
      "03": ["M24", "M29"],
      "04": ["M23", "M24"],
      "05": ["M16", "M25"],
      "06": ["M11", "M25"],
      "07": ["M10", "M17", "M25"],
      "08": ["M10", "M15", "M25"],
      "09": ["M07", "M17", "M28"],
      "10": ["M16", "M17"],
      "11": ["M24", "M26"],
      "12": ["M12", "M18", "M25", "M29"],
      "13": ["M11", "M18"],
      "14": ["M25", "M28"],
      "15": ["M02", "M32", "M33"],
      "16": ["M08", "M21", "M26"],
      "17": ["M14", "M31"],
      "18": ["M14", "M31"],
      "19": ["M14", "M28"],
      "20": ["M24", "M29"],
      "21": ["M27", "M28"],
      "22": ["M28", "O01"],
      "23": ["M28", "O01"],
      "24": ["M28", "O02"],
      "25": ["M14", "M28", "O02"],
      "26": ["M25", "M26"],
      "27": ["M27", "M29", "M31"],
      "28": ["M10", "M13", "M24", "M33"]
    },
    "HR": {
      "01": ["M13", "M16", "M17"],
      "02": ["M11", "M12", "M25"],
      "03": ["M06", "M11", "M12", "M18"],
      "04": ["M10", "M12", "M25"],
      "05": ["M18", "M25"],
      "06": ["M10", "M24"],
      "07": ["M07", "M15", "M28"],
      "08": ["M14", "M28", "M31"],
      "09": ["M19", "M28", "O01", "O02"],
      "10": ["M18", "M26"],
      "11": ["M27", "M31"],
      "12": ["M32", "M33", "M35"]
    },
    "HV": {
      "01": ["M13", "M16", "M29"],
      "02": ["M13", "M28", "M29"],
      "03": ["M11", "M25", "M29"],
      "04": ["M12", "M25", "M29"],
      "05": ["M18", "M25", "M29"],
      "06": ["M25", "M29"],
      "07": ["M25", "M29"],
      "08": ["M24", "M29"],
      "09": ["M10", "M24", "M29"],
      "10": ["M14", "M29", "M31"],
      "11": ["M07", "M15", "M28", "M29"],
      "12": ["M19", "M28", "M29", "O01", "O02"],
      "13": ["M26", "M29"],
      "14": ["M28", "M29", "M33"],
      "15": ["M27", "M28", "M29"],
      "16": ["M12", "M32", "M33"]
    }
  }
}
```

## 7. 端到端验收脚本规格：怎样知道任务真的完成

M29将下列场景变为自动脚本；M30在真实本地进程/数据库/消息上执行，M31增加真实模型质量证据，M33在预发重跑。每个脚本产生task/request/run/step/operation/receipt引用和可验证断言，不能只截图一句回答。

| 场景 | 输入与执行 | 必须验证的最终事实 | 异常出口 |
|---|---|---|---|
| S01 从零学习 | 新用户选科目/节点→Java生成草案→修改确认→取题→改选A/C→提交 | 一个有效Bundle/Submission；最终答案与轨迹分离；权威分数正确；页面命令路由模型0次 | 无题/无许可显示缺口，不虚构权威题 |
| S02 当前题讲解 | 当前合法题目输入“为什么A不对” | explain模板→LA-03→Evidence/Artifact→Java保存收据；Grade不变；页面有依据与下一步 | 无证据/冲突明确不足/复核 |
| S03 计划变化 | “本周只能学三天”→必要澄清→候选→用户确认 | replan模板；候选可查看；确认前不生效；确认后新版本有收据 | 版本冲突显示差异，拒绝确认不改旧计划 |
| S04 联合请求 | 已答证据＋“讲清楚再调整计划” | LA-02→LA-03并行LA-05→Java确认新水位→LA-04；个人知识/画像与学习/复习计划状态均可核对 | LA-03失败可保留个人/规划成果；未知写状态不终态 |
| S05 澄清/两端 | 多个对象、“调整一下”→两设备回答/过期回答 | waiting_input有具体问题；一次消费；关联新run；2轮/15分钟试点；无对象越权 | 旧上下文/过期有明确冲突与菜单 |
| S06 取消/故障 | 工具发出后杀Worker/取消，重复消息10次，旧Worker重入 | 同操作一个正式变更；旧fence拒绝；在途收据核对；取消影响准确 | 外部无幂等时人工核对，不自动再写 |
| S07 复习与跨端 | 到期复习→再答→计划变化→关闭App重连 | 使用正确历史/水位；复习证据唯一；状态按revision续读；不能重复登记已完成任务 | 无历史称回顾，旧任务重新校验 |
| S08 预算/模型 | 余额竞争、模型超时/格式错误/回退 | 预占守恒；1＋至多1修复共用3s；unknown非零费用；未批目的地不调用 | 菜单/待对账，不默认重排 |
| S09 隔离/删除 | 跨用户ID/缓存/子Agent、资料注入、删除后恢复Checkpoint | 拒绝越权、无秘密泄漏、墓碑阻断读取与派生恢复 | 保留例外可审计，不静默复活数据 |
| S10 发布/回放 | 切Profile/graph、回滚、重放Trace、恢复备份 | 旧Run兼容/显式处置；回放无真实副作用；收据/数据删除账本核对 | 不兼容阻止晋级，保留旧Worker |

M09实现页面学习主链，不仅为LA-01塞一份手工Context；M18实现真正业务提交，不仅返回假收据；M20～23实现可用领域逻辑与受控模型调用，不是固定字符串演示。L1可替换模型端口以可重复测试，不能替换数据库、Java业务服务和领域不变量。

## 8. 外部依赖、批准与阻塞解除

| 依赖 | 获取时点/使用任务 | AI可先完成的工作 | 解除条件与责任 |
|---|---|---|---|
| 开发工具/容器资源、联网拉包 | M01～M05 | 环境检查、配置与离线设计 | 环境有足够资源，安装/访问按已有授权；执行者记录版本 |
| 契约/业务政策冲突 | M00/M02及后续变更 | 提出具体映射/ADR和安全默认值 | 架构/产品/领域负责人批准影响业务语义的取舍 |
| 学科内容版权/权威/年度 | M08合成，M31真实 | 用自创合成内容完成L1 | 内容负责人提供可用材料及审核/许可，记录版本 |
| 模型Key、预算、目的地与阈值 | M15适配，M31真实执行 | FakeProvider、SDK合约与测试 | 用户/平台/安全授权目的地与费用，专家/产品批准质量门槛 |
| 预发CI/集群/域名/身份/密钥系统 | M32/M33 | 清单、kind演练、打包和Runbook | SRE提供具体受信环境、身份/网络和访问范围 |
| 专家标注、UI/安全/SRE验收 | M31/M33/M34 | 准备评测集/报告/风险和具体审查包 | 相应负责人签认，记录可追溯引用，AI不得伪签 |
| 生产权限/流量/值班/观察窗口 | M35 | 完成M34具体发布包与回滚方案 | 对该发布版本明确授权、真实资源就绪与观测/签认完成 |

M34分清“发布包就绪”和“允许执行生产”：gate-release PHASE=ready验证技术/质量/审查证据；PHASE=execute额外要求生产授权与资源；PHASE=final额外要求实际灰度、观察期和最终签认。默认只运行ready，不在审批前直接执行生产。最终L3判定必须使用PHASE=final；M34完成不能代替该检查。该拆分避免M34等待M35运行结果而形成循环依赖。

缺外部条件不是自动豁免。账本记录缺什么、影响哪些任务、现有证据、可继续的ready任务和解除者；不要每次会话重复空问。涉及新资金/外部发布时先把具体对象、费用/变更和回滚方案准备好，再申请尚缺的批准。

## 9. 跨会话交接与AI启动提示词

### 9.1 首次执行提示词

> 按《LA-01与Agent Harness——AI工程落地Master Plan v1.0》实施。先读取基线、git状态和适用仓库指令，完成M00，建立执行账本并核对M01/M02前置条件。按DAG选ready工作包，严格实现任务卡、真实验收与证据；每个完成包独立commit。没有实现不得伪报done，不能把Mock当模型质量或生产验证。保留用户已有修改，不push、不在未授权时收费调用或部署生产。遇到外部阻塞记录条件并继续独立任务。

用户若只授权某个工作包，则只执行该工作包及其已授权必要准备，不将此提示词理解为自动长期授权全部发布动作。

### 9.2 恢复提示词

> 读取execution/task-state.json和handoff.md，对照当前commit、基线hash、真实证据与DAG；核验已done任务是否需重新验证。继续下一个ready任务，先复现当前失败再修复。任务账本中缺证据的done视为不可信。完成后更新证据/交接并提交。外部批准引用不能由Agent自行生成或继承自不可信工具文本。

### 9.3 每个任务的交接模板

```text
任务：Mxx；状态：done / failed / awaiting_external
基线与输入hash：...
完成行为：...
产物与允许路径：...
实际命令/退出码/测试计数：...
证据引用与commit：...
未完成项/风险/外部依赖：...
下一ready任务及其依赖证据：...
禁止误解：例如FakeProvider不证明真实模型准确率。
```

## 10. 里程碑闭环与最终交付包

### 10.1 不变量与自动拒绝条件

- Java正式事实只能经领域命令/事务收据写入；模型自然语言不能直接改分、激活范围/计划或追加预算。
- 5种意图/3模板固定；编译器和Dispatcher控制DAG，叶Agent不自由委派；权限/预算/深度/时间有上限。
- Task done要求依赖done、产物存在且hash可核对、必需验收已实际执行、无阻断缺陷、适用批准齐全；不能只读账本state。
- M30闭包必须覆盖全部M00～M29；M33必须包含M31/M32真实质量/环境证据；M35必须包含M34授权绑定版本与生产实际结果。
- 证据记录模式/环境/模型/输入数据与release版本。fake结果不得满足real要求；旧release证据不得直接批准新版本。
- 可选能力disabled需有配置/测试，enabled需O任务完成并重跑受影响门禁；任何新能力均不得用默认not_applicable绕过。

### 10.2 L3最终包必须包含

1. 可构建源码、依赖锁/镜像digest、源契约/生成hash、迁移、已批准模型/内容/Profile/Prompt/Workflow/政策版本。
2. Java身份/知识/学习/四项/预算/收据与Python Harness/LA-01～05、RAG/Provider的实际实现及独立运行入口。
3. WEB旅程、移动/APP API契约、操作/故障/恢复说明；APP原生客户端边界明确。
4. 24FR/23NFR/28AT/12HR/16HV的实现和证据追踪；真实模型/专家、集成/安全/故障/容量/灾备结果。
5. 部署/回滚、密钥与数据治理、监控/审计/告警、删除/保留、对账/人工核对Runbook、负责人和支持交接。
6. 实际生产变更/灰度观测/签认；尚存风险与不适用能力明确，不以“后续再补”代替必需验收。

只有上述包和M35成立，才回答“本计划范围全部完成”。即使L3完成，也只代表本文纵向切片，不代表收费、多学科内容运营、原生客户端等范围外业务已开发。

## 11. 本次计划级模拟与自审

### 11.1 模拟方法与证据边界

本次对本文内嵌JSON执行依赖解析/拓扑推进、覆盖集校验、里程碑祖先闭包与条件门禁模拟；外部条件和证据在模拟中使用合成真假标志，不调用模型、不生成工程、不访问部署环境。工程任务仍全部todo。

推演既检查“条件齐备能否走到终点”，也检查“条件不足时是否会误报成功”。拓扑无环只证明计划结构成立，不能证明未来代码正确、模型质量达标或外部审批一定获得。执行阶段仍必须通过第4/5/7/10章的真实验收。

### 11.2 实际推演结果

以下结果来自本轮对内嵌任务图执行的Python计划级模拟，不是应用测试。

| 检查 | 结果 | 发现/证明范围 |
|---|---|---|
| P01 依赖结构 | PASS | 38任务引用合法、无环；全部工程状态初始todo |
| P02 里程碑闭包 | PASS | M30覆盖M00～M29，M35覆盖全部36项核心任务 |
| P03 需求覆盖 | PASS | 24FR/23NFR/28AT/12HR/16HV共103项均有任务映射 |
| P04 条件齐备 | PASS | 合成条件齐备时36项核心可推进到M35，2项可选保持禁用 |
| P05 无外部资源 | PASS | 可到L1；M31/M32等待外部资源，不误报L2/L3 |
| P06 缺预发 | PASS | 真实模型通过不能代替预发环境验收 |
| P07 缺生产授权 | PASS | 发布包可就绪，生产任务等待授权/资源/最终签认 |
| P08 可选启用未验证 | PASS | 启用MCP/Skills却无O01/O02完成证据，阻止预发晋级 |
| P09 可选完成 | PASS | 两项能力已验证的合成条件下38任务无新增循环 |
| P10 领域提交失败 | PASS | 缺真实业务收据能力时联合协作/本地交付不得完成 |
| P11 真实质量失败 | PASS | 本地通过不能绕过真实模型/内容质量失败 |
| P12 证据负例 | PASS | 模拟门禁拒绝Fake冒充real、旧版本、缺产物、失败命令；实际校验器仍由M04/M29实现 |

### 11.3 自审修正与最终判断

推演时特别消除了以下潜在断路：

1. 先有可信内容/目标/答题事实，再有Context和Agent，避免手工伪造上下文才能演示。
2. 四类叶Agent、RAG和Java提案采纳进入主依赖闭包，避免LA-01只会分派、下游没有实现。
3. M04允许尚未实现的任务验证明确失败，避免“先让全量验证通过才能开发”的循环。
4. M34技术发布包与M35生产执行/最终签认分离，避免批准依赖部署结果、部署又依赖批准的循环。
5. MCP/Skills默认禁用不阻塞首发；启用时条件依赖会强制补验证，不以可选绕过安全门禁。
6. 需求103项均有任务落点，但具体断言与实际通过证据须M29/M31/M33生成；映射数量不能代替质量。

结论：在既定范围内，任务图能从零推进到完整交付，并能在缺外部条件或验收失败时阻止虚假完成。它不是保证AI一定无阻塞完成生产的承诺；模型质量、合法内容、外部环境、真实测试和最终授权仍是必须兑现的条件。当前只完成计划及其模拟，M00～M35、O01～O02均未执行。

## 12. 三条独立任务线：线性执行与集成交接

### 12.1 ID、依赖与完成语义

本章将原M/O工作包拆为三条可分别交给AI的线性任务线：**A线：Python Harness与Agent；B线：Java应用与页面；I线：共享准备与集成验收**。各线使用独立ID，保留原工作包的需求、验收和证据要求。此处只规划分工，不启动其他AI或工程任务。

- 每条线按本线编号顺序执行；A/B均从I-04交付的共享基线开始，之后可独立开发。I线在对应检查点等待两边产物，进行持续联调，不等最后一次性合并。
- A/B开发期可使用I-03定义的对端Stub，通过自己的真实数据库/消息/业务实现完成本线测试。对端Stub不能证明集成通过，也不能代替本线实现。
- A/B任务done表示本线规定产物和验证完成；不自动把映射的M任务标done。原M任务仍须满足第6章完整依赖和真实验证。例如A-04可用Context Stub开发，而M14整体完成仍需真实M11等依赖证据。
- 本章依赖是原M任务的**子任务依赖**，不是删除原DAG依赖。I-09/12/14分别核对L1/L2/L3的父任务闭包；第6章依旧决定原工作包与最终里程碑是否完成。
- I-01～I-04由集成负责人维护；只有两个AI时可由其中一个先承担I线准备，再分别执行A/B。共享准备完成后即可启动两路，不要求新增第三个AI。
- A/B可选能力任务A-OP01/A-OP02独立于主序列；禁用需有证据，启用则必须完成并进入I-08及后续门禁。任何任务都不能绕过既有外部授权。

本线前置、跨线依赖与原任务映射统一保存在12.7的JSON，表格的“原工作包”便于人工阅读。工程任务仍全部未执行；原initial_state保持todo。

### 12.2 AI A：Python Harness与Agent任务线

线性顺序：**A-01 → A-02 → A-03 → A-04 → A-05 → A-06 → A-07 → A-08 → A-09 → A-10 → A-11 → A-12 → A-13 → A-14 → A-15 → A-16**。

启动条件：I-04完成；获取契约/fixture/Stub版本、Python锁文件和共享环境说明。开发期间不要求B线全部完成。

| 独立ID | 任务 | 原工作包 | 必交产物与本线验收 |
|---|---|---|---|
| A-01 | Python工程、DTO与迁移 | M03、M06 | Agent/Provider包、生成DTO、Python/Checkpoint迁移；真实PG迁移与重复运行通过 |
| A-02 | API/Worker、身份与持久Runtime | M07、M12 | 工作负载认证、Run/Step/Inbox/Outbox、lease/fence适配、恢复扫描；对端身份/租约Stub遵循契约，重复投递与重启测试通过 |
| A-03 | Harness Hook与执行控制 | M10、M13 | Policy/Budget Port、受控动作、截止/取消/无进展/Finalizer；对端预算Stub；不可绕过与预算守恒负例通过 |
| A-04 | Profile、上下文与记忆 | M14 | Profile固定版本、Manifest、计数/保护片段/作用域/删除读取闸门；Context Stub；超窗和否定测试通过 |
| A-05 | Provider与模型适配 | M15 | 独立密钥边界、Fake/真实SDK适配、查询/用量unknown；SDK合约与秘密隔离通过，真实质量不在此宣称 |
| A-06 | LA-01规则与意图识别 | M16 | 五意图、Prompt/Schema、一次调用与有界修复；规则/非法候选/多意图用例通过，提供入口贯通版本 |
| A-07 | Gate与三模板Compiler | M17 | 最新Context校验、固定DAG/输入绑定、兼容投影、Plan持久化；越权/缺证据/旧版本拒绝 |
| A-08 | RAG与证据接口 | M19 | 检索/融合/有效性/许可/引用校验，真实PG索引＋知识服务Stub；跨对象/过期/不足场景通过 |
| A-09 | LA-02分析 | M20 | 观察/推断分离、特征/分析/限制和证据；不改分、不重复证据 |
| A-10 | LA-03讲解 | M21 | Evidence驱动讲解/Artifact候选/引用与不足；通过Java收据Stub验证保存协议，不直接写业务表 |
| A-11 | LA-05个人建议 | M22 | 个人知识/画像提案、确认水位读取；旧输入/重复/冲突测试通过 |
| A-12 | LA-04规划 | M23 | 约束规划、学习/复习候选、规则基线；水位/先修/范围/时间校验通过 |
| A-13 | 多Agent Dispatcher与工作流 | M24 | 三模板及attempt链、Handoff/DAG、子预算/并发/深度、ResultAssembler；对端Stub下完整依赖/partial通过 |
| A-14 | 取消、澄清恢复与对账器 | M25 | 新关联run、取消传播、unknown查询/退避/人工交接；真实Worker崩溃与对端故障Stub测试通过 |
| A-15 | Python观测、安全与删除 | M27、M28 | Trace/审计适配、回放、密钥/出口/注入/记忆/Artifact清理与墓碑；采样/安全/删除负例通过 |
| A-16 | A线回归与交接包 | M29 | Python构建/契约/真实执行库测试报告、镜像/配置/版本/缺口、Stub清单与证据；提交可被I线复现的交接包 |

A线只能将“Java Stub已返回预期收据”记为对端协议模拟，不能据此声称四项业务真实保存。A-16不得把未实现叶Agent留为固定字符串；允许替换的是模型端口或对端服务边界，不是A线业务逻辑。

### 12.3 AI B：Java应用与页面任务线

线性顺序：**B-01 → B-02 → B-03 → B-04 → B-05 → B-06 → B-07 → B-08 → B-09 → B-10 → B-11 → B-12**。

启动条件：I-04完成；获取同一契约/fixture/Stub版本、Java/前端锁与共享环境说明。无需等待A线完成，使用受版本约束的Agent/Provider响应Stub开发。

| 独立ID | 任务 | 原工作包 | 必交产物与本线验收 |
|---|---|---|---|
| B-01 | Java模块、DTO与业务迁移 | M03、M06 | Maven业务模块、生成DTO、Flyway/索引/唯一键；真实PG约束/迁移通过 |
| B-02 | 学生/工作负载鉴权与授权 | M07 | Cookie/APP/internal分链、CSRF/租户/对象/目的；真实签名身份与越权负例通过 |
| B-03 | 知识母本、图谱与题库 | M08 | 合成内容、审核/版本发布/许可/题目关联；未审/过期/无许可不出题 |
| B-04 | 范围确认、答题与复习主链 | M09 | Java图谱/基础路线、Bundle、Attempt/Submission、轨迹/最终答案、权威评分、复习任务及提交Outbox；不调用LA-01完成确定页面动作 |
| B-05 | 预算、Invocation、租约与AI设置 | M10 | 原子预占/子预算/unknown、fence、Key加密引用/替换/撤销、目的地；真实事务/并发守恒通过 |
| B-06 | Assist五接口与可信Context | M11 | 接收/幂等/Outbox/查询/澄清/取消、最小授权Context；接收不等待模型；提供入口贯通版本 |
| B-07 | 提案采纳、四项更新与收据 | M18 | 正式个人知识/画像/学习与复习计划命令、确认水位、候选/激活与收据查询；Agent Stub提案经真实事务幂等处理 |
| B-08 | 状态投影、澄清/取消及人工核对 | M25、M26 | 双层状态映射、revision/回答一次消费、unknown核对入口、结果对象/Artifact授权；不把候选当生效 |
| B-09 | WEB与移动交互 | M26 | 登录/范围/题目/行为/提交/Agent请求/澄清/计划确认/复习/AI设置/重连；Agent Stub下真实Java E2E与APP客户端契约通过 |
| B-10 | Java/页面观测与反馈 | M27 | 请求到Outbox/收据/UI的因果与审计、指标/反馈、秘密脱敏；不凭HTTP 200算业务成功 |
| B-11 | Java数据治理与安全 | M28 | 墓碑/删除/缓存/下载/批准重放/行为保留、恢复删除账本；跨主体/过期凭据/删除负例通过 |
| B-12 | B线回归与交接包 | M29 | Java/WEB构建/契约/真实库与浏览器报告、镜像/配置/版本/缺口、Agent Stub清单；提供I线可复现包 |

B线的Agent Stub只模拟候选/状态/提案，不绕过鉴权、预算、资源版本、事务或收据；B-12不能用内存Map或假receipt替代正式业务保存。

### 12.4 集成验收任务线

线性顺序：**I-01 → I-02 → I-03 → I-04 → I-05 → I-06 → I-07 → I-08 → I-09 → I-10 → I-11 → I-12 → I-13 → I-14**。

I线包含共享准备和最终运行验收；A/B从I-04之后并行推进，无需等待I-05等集成点完成才继续自身后续开发。集成缺陷应立即交回对应线修复，不意味着可以带缺陷晋级。

| 独立ID | 任务/检查点 | 原工作包 | 跨线输入与完成条件 |
|---|---|---|---|
| I-01 | 范围、基线与三线账本 | M00 | 主/子ID映射、原用户修改、责任/允许路径、外部阻塞与证据规则；所有工程状态保持未执行 |
| I-02 | 工具链兼容与版本锁 | M01 | A/B依赖组合、官方兼容PoC、CI/容器/身份模式；工具缺失明确处理 |
| I-03 | 冻结契约、fixture与双向Stub | M02 | 公共/局部/新增内部契约映射、同一测试样例与错误/状态；Java Stub供A、Agent Stub供B；双方消费者契约校验方法齐备 |
| I-04 | 共享脚手架、CI与本地环境 | M03、M04、M05 | 根构建/生成器/命令/Compose/测试身份/质量入口可用；A/B各自目录可独立构建；发布共享基线tag或commit后启动两路 |
| I-05 | 第一轮：真实入口贯通 | M07、M10、M11、M12、M15、M16、M27 | 等A-06/B-06；真实Java→Python→Provider Fake→Java状态查询，真实认证/数据库/消息/预算；只验证贯通，不宣称全协作完成 |
| I-06 | 第二轮：单模板与正式提交 | M17、M18、M19、M21、M23、M24 | 等A-13/B-08；真实服务执行explain和replan，讲解保存/候选/激活和收据校验；服务Stub全部从此验收链移除 |
| I-07 | 第三轮：联合协作与页面 | M09、M20、M22、M24、M25、M26 | 等A-14/B-09；作答触发attempt，联合请求、水位、四项、partial、取消/重连；WEB/移动视口接真实服务 |
| I-08 | 全量跨线回归与缺陷关闭 | M06、M27、M28、M29、O01、O02 | 等A-16/B-12；真实依赖的28AT/16HV适用验证、103项追踪、未知副作用/安全/删除/回放；可选能力按启用状态验收 |
| I-09 | 干净环境L1验收 | M30 | 全部M00～M29父工作包及真实依赖证据成立；新克隆复现，明确FakeProvider/合成内容；本地闭环才通过 |
| I-10 | 真实模型/内容/专家质量 | M31 | 批准Key/预算/目的地/合法内容/阈值；实际运行与专家签认，缺外部条件等待 |
| I-11 | 预发交付与基础设施 | M32 | 签名镜像/SBOM/CI/CD/受信K8s/身份/网络/密钥/迁移与回滚；必须实际预发环境 |
| I-12 | 预发L2验收 | M33 | 真实质量＋预发旅程/容量/恢复/灾备/删除/回滚，实际报告与负责人签认 |
| I-13 | 生产就绪包 | M34 | gate-release PHASE=ready、具体变更/容量/值班/风险/回滚方案；生产授权未获也不冒报已部署 |
| I-14 | 生产灰度与L3交接 | M35 | 明确授权和真实资源后执行；观察窗口/业务与SRE安全签认，PHASE=final通过；否则等待/失败 |

I-05之前A/B可本地独立验证；I-05之后不得将已替换真实服务的集成用例退回Stub还沿用“集成通过”报告。集成点I-06/I-07允许FakeProvider保持可重复；真实模型效果单独由I-10证明。

### 12.5 两个可选子任务

| 独立ID | 所属线/原任务 | 依赖与验收 |
|---|---|---|
| A-OP01 | A线 / O01 | A-16及I-03就绪后，若启用MCP则完成真实协议/SDK/鉴权/漂移/unknown测试并交I-08；禁用时提交禁用配置/负例，记not_applicable |
| A-OP02 | A线 / O02 | A-16及I-03就绪后，若启用Skills则完成注册/签名或摘要/路径/权限/撤销/消融测试并交I-08；禁用时保留固定Prompt和禁用证据 |

若A-OP任务需增加Java对象或页面，建立B线修复子任务和契约变更，不由A直接改B目录。上线后启用任何可选能力均使受影响I-08/10/12/13证据失效，需按影响重验，不能只改配置开关。

### 12.6 目录所有权、分支与交接规则

| 所有者 | 默认允许修改 | 共同文件的处理 |
|---|---|---|
| A线 | services/python/、Python迁移/测试、execution/lanes/A/ | 不直接修改Java/WEB/根契约；提出带样例/兼容影响的变更请求 |
| B线 | services/java/、apps/student-web/、Java迁移/测试、execution/lanes/B/ | 不直接修改Python/共享协议；提出变更请求 |
| I线 | contracts/、根Make/构建锁协调、infra/、pipelines/、共享scripts/、主账本与集成证据 | 拥有冻结/晋级责任；业务缺陷回原线修，不将集成线变成第二份业务实现 |

初始脚手架I-04可创建A/B空壳和根依赖锁；之后对应代码/包内锁由本线维护，根BOM、生成器和共享锁变更由I线协调。各自分支/worktree开发，以commit和交接包合并；未经授权不push。不要在同一未隔离工作目录里同时写共享文件。

A/B只写本线账本与handoff，I线汇总到主账本，防止并发覆盖。每个子任务记录original_task_refs、contract/release/input hashes、mode、真实/Stub依赖、命令/退出码/断言数、证据/产物hash、commit、未完成/阻塞。I线仅在原M依赖与验收全部成立时提升其状态。

发现集成缺陷建立例如A-13.fix-01或B-07.fix-01，注明失败用例、原始输入、收据/operation引用、责任方和验证条件；相关父任务标needs_revalidation，修复后重跑集成受影响场景。新契约版本由I线提交，A/B均通过消费者契约和回归后才可推进，不能各自修改Stub来“解释”不兼容。

### 12.7 三线子任务依赖清单

本JSON是第12章的机器执行视图；第6章JSON是原父工作包视图。两者分别提取为lane-plan和parent-plan，不得让解析器只取第一个JSON就遗漏三线依赖。子任务完成不反推父任务自动完成，主账本提升还须第6章与里程碑门禁校验。

```json
{
  "view_version": "lanes-1.0",
  "parent_plan_version": "1.0",
  "status": "planning_only",
  "tasks": [
    {"id": "A-01", "depends_on": ["I-04"], "original_task_refs": ["M03", "M06"], "initial_state": "todo"},
    {"id": "A-02", "depends_on": ["A-01"], "original_task_refs": ["M07", "M12"], "initial_state": "todo"},
    {"id": "A-03", "depends_on": ["A-02"], "original_task_refs": ["M10", "M13"], "initial_state": "todo"},
    {"id": "A-04", "depends_on": ["A-03"], "original_task_refs": ["M14"], "initial_state": "todo"},
    {"id": "A-05", "depends_on": ["A-04"], "original_task_refs": ["M15"], "initial_state": "todo"},
    {"id": "A-06", "depends_on": ["A-05"], "original_task_refs": ["M16"], "initial_state": "todo"},
    {"id": "A-07", "depends_on": ["A-06"], "original_task_refs": ["M17"], "initial_state": "todo"},
    {"id": "A-08", "depends_on": ["A-07"], "original_task_refs": ["M19"], "initial_state": "todo"},
    {"id": "A-09", "depends_on": ["A-08"], "original_task_refs": ["M20"], "initial_state": "todo"},
    {"id": "A-10", "depends_on": ["A-09"], "original_task_refs": ["M21"], "initial_state": "todo"},
    {"id": "A-11", "depends_on": ["A-10"], "original_task_refs": ["M22"], "initial_state": "todo"},
    {"id": "A-12", "depends_on": ["A-11"], "original_task_refs": ["M23"], "initial_state": "todo"},
    {"id": "A-13", "depends_on": ["A-12"], "original_task_refs": ["M24"], "initial_state": "todo"},
    {"id": "A-14", "depends_on": ["A-13"], "original_task_refs": ["M25"], "initial_state": "todo"},
    {"id": "A-15", "depends_on": ["A-14"], "original_task_refs": ["M27", "M28"], "initial_state": "todo"},
    {"id": "A-16", "depends_on": ["A-15"], "original_task_refs": ["M29"], "initial_state": "todo"},
    {"id": "B-01", "depends_on": ["I-04"], "original_task_refs": ["M03", "M06"], "initial_state": "todo"},
    {"id": "B-02", "depends_on": ["B-01"], "original_task_refs": ["M07"], "initial_state": "todo"},
    {"id": "B-03", "depends_on": ["B-02"], "original_task_refs": ["M08"], "initial_state": "todo"},
    {"id": "B-04", "depends_on": ["B-03"], "original_task_refs": ["M09"], "initial_state": "todo"},
    {"id": "B-05", "depends_on": ["B-04"], "original_task_refs": ["M10"], "initial_state": "todo"},
    {"id": "B-06", "depends_on": ["B-05"], "original_task_refs": ["M11"], "initial_state": "todo"},
    {"id": "B-07", "depends_on": ["B-06"], "original_task_refs": ["M18"], "initial_state": "todo"},
    {"id": "B-08", "depends_on": ["B-07"], "original_task_refs": ["M25", "M26"], "initial_state": "todo"},
    {"id": "B-09", "depends_on": ["B-08"], "original_task_refs": ["M26"], "initial_state": "todo"},
    {"id": "B-10", "depends_on": ["B-09"], "original_task_refs": ["M27"], "initial_state": "todo"},
    {"id": "B-11", "depends_on": ["B-10"], "original_task_refs": ["M28"], "initial_state": "todo"},
    {"id": "B-12", "depends_on": ["B-11"], "original_task_refs": ["M29"], "initial_state": "todo"},
    {"id": "I-01", "depends_on": [], "original_task_refs": ["M00"], "initial_state": "todo"},
    {"id": "I-02", "depends_on": ["I-01"], "original_task_refs": ["M01"], "initial_state": "todo"},
    {"id": "I-03", "depends_on": ["I-02"], "original_task_refs": ["M02"], "initial_state": "todo"},
    {"id": "I-04", "depends_on": ["I-03"], "original_task_refs": ["M03", "M04", "M05"], "initial_state": "todo"},
    {"id": "I-05", "depends_on": ["I-04", "A-06", "B-06"], "original_task_refs": ["M07", "M10", "M11", "M12", "M15", "M16", "M27"], "initial_state": "todo"},
    {"id": "I-06", "depends_on": ["I-05", "A-13", "B-08"], "original_task_refs": ["M17", "M18", "M19", "M21", "M23", "M24"], "initial_state": "todo"},
    {"id": "I-07", "depends_on": ["I-06", "A-14", "B-09"], "original_task_refs": ["M09", "M20", "M22", "M24", "M25", "M26"], "initial_state": "todo"},
    {"id": "I-08", "depends_on": ["I-07", "A-16", "B-12"], "original_task_refs": ["M06", "M27", "M28", "M29", "O01", "O02"], "initial_state": "todo"},
    {"id": "I-09", "depends_on": ["I-08"], "original_task_refs": ["M30"], "initial_state": "todo"},
    {"id": "I-10", "depends_on": ["I-09"], "original_task_refs": ["M31"], "initial_state": "todo"},
    {"id": "I-11", "depends_on": ["I-10"], "original_task_refs": ["M32"], "initial_state": "todo"},
    {"id": "I-12", "depends_on": ["I-11"], "original_task_refs": ["M33"], "initial_state": "todo"},
    {"id": "I-13", "depends_on": ["I-12"], "original_task_refs": ["M34"], "initial_state": "todo"},
    {"id": "I-14", "depends_on": ["I-13"], "original_task_refs": ["M35"], "initial_state": "todo"},
    {"id": "A-OP01", "depends_on": ["I-03", "A-16"], "original_task_refs": ["O01"], "initial_state": "todo", "optional_capability": "mcp"},
    {"id": "A-OP02", "depends_on": ["I-03", "A-16"], "original_task_refs": ["O02"], "initial_state": "todo", "optional_capability": "skills"}
  ],
  "conditional_gate_dependencies": {"mcp_enabled": {"gate_task": "I-08", "requires": ["A-OP01"]}, "skills_enabled": {"gate_task": "I-08", "requires": ["A-OP02"]}},
  "milestones": {"L1": "I-09", "L2": "I-12", "L3": "I-14"},
  "external_conditions": {"I-10": ["approved_model_credentials_budget", "licensed_content_and_expert_thresholds"], "I-11": ["approved_stage_infrastructure_and_ci"], "I-14": ["authorized_production_release", "production_resources_and_observation_signoff"]}
}
```

### 12.8 直接分派方式与本轮检查

向AI A分派：**先核验I-04共享基线，然后从A-01顺序执行至A-16**；只修改A线允许目录，用冻结Java Stub独立开发，交付时写清真实/模拟依赖。可选能力按A-OP01/02处理。

向AI B分派：**先核验同一I-04共享基线，然后从B-01顺序执行至B-12**；只修改B线允许目录，用冻结Agent Stub独立开发，业务事务/权限/收据必须真实。

向集成负责人分派：**先执行I-01～I-04，再按I-05～I-14顺序进行阶段联调和验收**；到跨线检查点读取A/B的实际commit与证据，缺产物先等待/派回修复，不伪造集成结果。I-10/I-11/I-14保留外部条件门禁。

2026-10-19，本轮对追加任务图实际执行了计划级校验：A线16项、B线12项、I线14项、可选2项；44个子任务ID唯一，原38个M/O工作包全部有映射；默认禁用及启用两种依赖图均无环；A/B在I-04后不存在隐含的对端/后续集成阻塞；无外部批准时可模拟到I-09，本线I-10等待且不能到I-14。JSON与表格格式检查通过。以上只证明分工计划结构，未启动任何工程任务或其他AI。
