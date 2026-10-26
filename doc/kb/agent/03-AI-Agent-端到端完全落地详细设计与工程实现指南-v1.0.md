# 企业级 AI Agent 端到端完全落地详细设计与工程实现指南 (v1.0)

| 属性 | 内容 |
|---|---|
| 文档状态 | 2026-10-25；v1.0 基线版本；指导 100% 端到端闭环工程落地与交付 |
| 目标定位 | 消除抽象概念悬空，提供包含运行时、网关、自包含 RAG、MCP 工具沙箱及 EvalOps 评测的完整代码级工程规范 |
| 上位全景指南 | [01-AI-Agent-企业级架构知识体系全景指南-v1.0.md](./01-AI-Agent-企业级架构知识体系全景指南-v1.0.md) |
| 原理参考 | [02-AI-Agent-Harness-受控宿主深度原理解析-v1.0.md](./02-AI-Agent-Harness-受控宿主深度原理解析-v1.0.md) |

---

## 目录
- [一、 端到端工程套件拓扑与代码结构](#一-端到端工程套件拓扑与代码结构)
- [二、 核心数据库表结构物理 DDL (PostgreSQL)](#二-核心数据库表结构物理-ddl-postgresql)
- [三、 套件 1：Harness 运行时受控内核核心实现](#三-套件-1harness-运行时受控内核核心实现)
- [四、 套件 2：LLMOps 网关与确定性 FakeProvider](#四-套件-2llmops-网关与确定性-fakeprovider)
- [五、 套件 3：自包含 Hybrid RAG 检索与 EvidencePack 校验](#五-套件-3自包含-hybrid-rag-检索与-evidencepack-校验)
- [六、 套件 4：可观测性与自动化 EvalOps 评测流水线](#六-套件-4可观测性与自动化-evalops-评测流水线)
- [七、 零依赖一键本地启动与 CI/CD 验收指南](#七-零依赖一键本地启动与-cicd-验收指南)

---

## 一、 端到端工程套件拓扑与代码结构

整个交付体系分为 4 个核心工程组件，支持在单机纯离线环境（Fake 模式）或生产微服务环境（真实模型与云存储）中无缝切换运行：

```text
cogniva/
├── infra/                                 # 容器编排与基础设施配置
│   ├── docker-compose.yml                 # PostgreSQL(pgvector), RabbitMQ, OpenTelemetry
│   └── otel-collector-config.yaml         # Tracing 导出配置
│
├── services/
│   ├── cogniva-learning-agent/            # 【套件 1: 核心运行时服务】
│   │   ├── src/cogniva_agent/
│   │   │   ├── domain/                    # 纯净领域实体: Run, Step, State, ContextManifest
│   │   │   ├── harness/                   # 宿主内核: kernel.py, hooks.py, lease.py, reconciler.py
│   │   │   ├── workflows/                 # LangGraph 拓扑图与条件路由
│   │   │   └── ports/                     # 六边形端口规范
│   │   └── tests/harness/                 # 9 阶段 Hook、CAS 脑裂冲突、重投单测
│   │
│   ├── cogniva-model-provider/            # 【套件 2: LLMOps 网关服务】
│   │   ├── src/cogniva_provider/
│   │   │   ├── adapters/fake_provider.py  # 100% 确定性离线 Mock 实现
│   │   │   ├── adapters/openai_adapter.py # 生产出网适配
│   │   │   └── server/                    # 统一模型 API 服务
│   │   └── tests/
│   │
│   └── cogniva-knowledge-service/         # 【套件 3: 自包含 RAG 与工具服务】
│       ├── src/cogniva_knowledge/
│       │   ├── schema/                    # 四层知识库表结构与 DTO
│       │   ├── search/hybrid_search.py    # BM25 + pgvector 混合检索引擎
│       │   ├── evidence/validator.py      # EvidencePack 证据链充分性判定器
│       │   └── tools/mcp_server.py        # 标准 MCP 工具服务与隔离沙箱
│       └── tests/
│
└── evalops/                               # 【套件 4: 持续评测与质量回归套件】
    ├── benchmarks/golden_dataset.json     # 黄金基准评测数据集 (含边界反例)
    ├── metrics/g_eval.py                  # LLM-as-a-Judge 打分与忠实度校验器
    └── run_eval_pipeline.py               # CI/CD 自动化回归门禁脚本
```

---

## 二、 核心数据库表结构物理 DDL (PostgreSQL)

系统状态持久化采用 PostgreSQL，启用 `pgvector` 扩展支持稠密向量检索：

```sql
-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. 会话运行实例表 (支持租约与单调 CAS fencing_token)
CREATE TABLE agent_runs (
    run_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    fencing_token BIGINT NOT NULL DEFAULT 1,
    lease_owner VARCHAR(64),
    lease_expires_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(32) NOT NULL DEFAULT 'running', -- running, waiting_user, completed, failed
    total_token_reserved INT NOT NULL DEFAULT 0,
    total_token_used INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. 执行步骤与状态检查点表 (CAS 防脑裂)
CREATE TABLE agent_checkpoints (
    checkpoint_id VARCHAR(64) PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL REFERENCES agent_runs(run_id) ON DELETE CASCADE,
    step_number INT NOT NULL,
    fencing_token BIGINT NOT NULL,
    state_payload JSONB NOT NULL,
    context_manifest JSONB NOT NULL,
    receipt_summary JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_run_step UNIQUE (run_id, step_number)
);

-- 3. 幂等操作审计与未知对账表
CREATE TABLE agent_operations (
    operation_ref VARCHAR(128) PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL,
    tool_name VARCHAR(64) NOT NULL,
    input_hash VARCHAR(64) NOT NULL,
    idempotent_key VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL, -- pending, success, unknown, failed
    response_payload JSONB,
    retry_count INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. 自包含知识库四层投影表 (混合检索)
CREATE TABLE knowledge_nodes (
    node_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    scope VARCHAR(32) NOT NULL, -- public_gold, private_student
    title VARCHAR(256) NOT NULL,
    content TEXT NOT NULL,
    tsv_content TSVECTOR GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED,
    embedding vector(1536), -- 适配主流嵌入维度
    version_id VARCHAR(64) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX idx_knowledge_nodes_tsv ON knowledge_nodes USING GIN (tsv_content);
CREATE INDEX idx_knowledge_nodes_embedding ON knowledge_nodes USING hnsw (embedding vector_cosine_ops);
```

---

## 三、 套件 1：Harness 运行时受控内核核心实现

在 `services/cogniva-learning-agent/src/cogniva_agent/harness/kernel.py` 中，实现核心不可穿透驱动循环：

```python
"""Harness 核心受控执行驱动循环 (Advance Engine)"""
from typing import Any, Dict
from dataclasses import dataclass

@dataclass
class AdvanceResult:
    status: str
    fencing_token: int
    output_state: Dict[str, Any]
    receipt: Dict[str, Any] | None

class HarnessKernel:
    def __init__(self, hook_registry, checkpoint_repo, lease_service):
        self.hooks = hook_registry
        self.checkpoint_repo = checkpoint_repo
        self.lease_service = lease_service

    async def advance(self, run_id: str, client_token: int, inbound_event: Dict[str, Any]) -> AdvanceResult:
        # 1. on_run_load: 租约与租户合规核查
        run = await self.hooks.on_run_load(run_id, client_token)
        if not await self.lease_service.verify_lease(run, client_token):
            raise PermissionError("Lease expired or invalid fencing_token! Execution halted.")

        # 2. before_context: 组装与合规裁剪上下文
        context = await self.hooks.before_context(run, inbound_event)

        # 3. before_model: Token 原子预算预占
        budget_reservation = await self.hooks.before_model(run, context)

        # 4. 执行模型推理 (通过独立 Provider)
        raw_proposal = await self.hooks.call_model(run, context, budget_reservation)

        # 5. after_model: Schema 反序列化强校验，剥离非法提权
        validated_proposal = await self.hooks.after_model(run, raw_proposal)

        # 6. before_action: 宿主安全门禁签发 AuthorizedToolCall
        authorized_actions = await self.hooks.before_action(run, validated_proposal)

        # 7. after_action: 执行工具调用并记录幂等 operation_ref (处理未知超时)
        action_results = await self.hooks.after_action(run, authorized_actions)

        # 8. before_checkpoint: CAS 乐观锁持久化状态 (防止脑裂)
        new_token = client_token + 1
        await self.checkpoint_repo.save_checkpoint_cas(
            run_id=run_id,
            expected_token=client_token,
            new_token=new_token,
            state_data=action_results
        )

        # 9. before_finalize & after_finalize: 聚合终态收据与异步外发
        receipt = await self.hooks.before_finalize(run, action_results)
        await self.hooks.after_finalize(run, receipt)

        return AdvanceResult(
            status=run.status,
            fencing_token=new_token,
            output_state=action_results,
            receipt=receipt
        )
```

---

## 四、 套件 2：LLMOps 网关与确定性 FakeProvider

在 `services/cogniva-model-provider/src/cogniva_provider/adapters/fake_provider.py` 中，实现 100% 确定性离线 Mock，支持离线秒级跑通单元测试：

```python
"""确定性 FakeProvider: 离线生成合法结构化数据，无需调用外部商用大模型"""
import hashlib
from typing import Dict, Any

class FakeModelProvider:
    async def generate_response(self, prompt: str, schema_name: str) -> Dict[str, Any]:
        # 基于输入生成确定性稳定哈希，保证单测稳定
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]

        if schema_name == "ExplanationDraft":
            return {
                "thought_process": f"Verified with deterministic evidence hash: {prompt_hash}",
                "explanation": "基于母本知识点法条第 32 条，本案属于免责声明有效情形。",
                "cited_evidence_ids": ["EVID-LAW-0032"],
                "proposed_actions": []
            }
        elif schema_name == "PlanProposal":
            return {
                "recommended_tasks": ["TASK-PRACTICE-01", "TASK-REVIEW-02"],
                "total_estimated_minutes": 45,
                "confidence_score": 0.96
            }
        return {"result": "success", "hash": prompt_hash}
```

---

## 五、 套件 3：自包含 Hybrid RAG 检索与 EvidencePack 校验

在 `services/cogniva-knowledge-service/src/cogniva_knowledge/search/hybrid_search.py` 中实现混合检索：

```python
"""混合检索器: BM25 精确词项 + 稠密向量余弦相似度 + 证据链充分性判定"""
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class EvidenceItem:
    evidence_id: str
    source_type: str
    text_content: str
    score: float

class HybridRAGEngine:
    def __init__(self, db_session):
        self.db = db_session

    async def search(self, query: str, query_embedding: List[float], top_k: int = 5) -> List[EvidenceItem]:
        # PostgreSQL 联合全文检索与向量相似度
        sql = """
            SELECT node_id, scope, content,
                   (ts_rank(tsv_content, plainto_tsquery('simple', :query)) * 0.4 +
                    (1 - (embedding <=> :vector::vector)) * 0.6) as combined_score
            FROM knowledge_nodes
            WHERE is_active = TRUE
            ORDER BY combined_score DESC
            LIMIT :top_k;
        """
        result = await self.db.execute(sql, {"query": query, "vector": str(query_embedding), "top_k": top_k})
        rows = result.fetchall()
        return [
            EvidenceItem(
                evidence_id=r[0],
                source_type=r[1],
                text_content=r[2],
                score=float(r[3])
            ) for r in rows
        ]

    def validate_sufficiency(self, evidences: List[EvidenceItem], threshold: float = 0.75) -> bool:
        """证据充分性校验: 最高得分必须超过门槛，否则判定事实不足，拒绝幻觉输出"""
        if not evidences:
            return False
        return evidences[0].score >= threshold
```

---

## 六、 套件 4：可观测性与自动化 EvalOps 评测流水线

在 `evalops/metrics/g_eval.py` 中构建自动化质量门禁打分器：

```python
"""自动化 EvalOps 质量评估器: 工具匹配率、忠实度 (Faithfulness) 与幻觉检测"""
from typing import Dict, Any

class EvalOpsValidator:
    @staticmethod
    def evaluate_turn(prediction: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, float]:
        # 1. 工具调用准确度
        pred_tools = set(prediction.get("tools_called", []))
        expected_tools = set(ground_truth.get("expected_tools", []))
        tool_accuracy = 1.0 if pred_tools == expected_tools else 0.0

        # 2. 证据引用忠实度
        pred_cites = set(prediction.get("cited_evidence_ids", []))
        gold_cites = set(ground_truth.get("gold_evidence_ids", []))
        citation_recall = len(pred_cites & gold_cites) / len(gold_cites) if gold_cites else 1.0

        # 3. 结构合规性
        has_required_keys = all(k in prediction for k in ground_truth.get("required_keys", []))
        schema_pass = 1.0 if has_required_keys else 0.0

        return {
            "tool_accuracy": tool_accuracy,
            "citation_recall": citation_recall,
            "schema_pass": schema_pass,
            "overall_score": (tool_accuracy * 0.4 + citation_recall * 0.4 + schema_pass * 0.2)
        }
```

---

## 七、 零依赖一键本地启动与 CI/CD 验收指南

### 7.1 本地 100% 离线确定性跑通单测（不花一分钱，不调外部 API）
在工程根目录下执行：
```bash
# 1. 运行 Harness 核心 9 阶段拦截与 CAS 脑裂冲突测试
pytest services/cogniva-learning-agent/tests/harness -v

# 2. 运行自包含 Hybrid RAG 检索充分性测试
pytest services/cogniva-knowledge-service/tests -v

# 3. 运行离线 EvalOps 评测回归门禁
python evalops/run_eval_pipeline.py --mode=offline --dataset=evalops/benchmarks/golden_dataset.json
```

### 7.2 生产环境一键微服务启动
```bash
# 启动本地依赖 (Postgres + pgvector, RabbitMQ, OpenTelemetry Jaeger)
docker-compose -f infra/docker-compose.yml up -d

# 执行数据库迁移
alembic upgrade head

# 启动核心 Agent 服务与 Provider 网关
uvicorn cogniva_agent.adapters.api.main:app --port 8000 &
uvicorn cogniva_provider.server:app --port 8001 &
```
