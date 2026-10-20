# AI Agent Harness Enterprise Generic Scaffold Detailed Design v1.0

| Attribute | Content |
|---|---|
| Document Status | 2026-10-19; Enterprise Agent Runtime & Scaffold Architecture Specification; Implementation Guide for M03+ |
| Target System | Cogniva Platform (Cognition + Nova) Multi-Agent Collaborative Fleet & Generic Agentic Engineering |
| Upstream Architecture | [Generic Agent-Harness Reference Architecture & Engineering Specification v1.0](./通用Agent-Harness-参考架构与工程规范-v1.0.md) |
| Related Detailed Design | [Student Continuous Learning Multi-Agent Fleet Detailed Design v1.0](../design/学生持续学习-AI-Agent群详细设计-v1.0.md), [LA-01 Coordinator Agent Requirements & C4 Design v1.0](../design/agents/LA-01-学习协调Agent-需求与C4详细设计-v1.0.md) |
| Chinese Source File | [AI-Agent-Harness-企业级通用脚手架详细设计-v1.0.md](./AI-Agent-Harness-企业级通用脚手架详细设计-v1.0.md) |
| Core Mission | Build a high-availability, strongly isolated, crash-resilient, and auditable enterprise-grade Agent Harness scaffold to bridge the chasm between toy demos and mission-critical production systems. |

---

## 1. Architectural Positioning: LangGraph vs. Harness Host Control Ring

When engineering an enterprise-grade AI Agent system, a clear boundary must be established between the **"Graph Execution Engine"** and the **"Enterprise Controlled Host (Harness)"**.

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

### 1.1 The Role & Limitations of Open-Source Frameworks (LangChain / LangGraph / Deep Agent)
- **Role of the Open-Source Framework**: It functions as an algorithmic **"Directed Graph Engine & Local Scheduler"** (StateGraph, node/edge topologies, conditional branching, and transient checkpointers).
- **The Fatal "Happy-Path" Assumption**: Open-source SDKs implicitly assume the network never drops, worker processes never crash or get OOM-killed, external LLMs never timeout, and models can arbitrarily decide which tools to execute (`tool.run()`).
- **Commercial Boundary**: Open-source communities delegate multi-tenancy, secret management, distributed leasing, and compliance auditing to closed-source cloud SaaS (e.g., LangSmith / LangGraph Cloud), which cannot address on-premise private data governance, polyglot (Java + Python) transactional consensus, or deterministic offline testing.

### 1.2 The Core Mandate of the Harness (Enterprise Host)
- **Role of the Harness**: It acts as the outer **"Host Control Ring & Distributed Supervised Runtime"**.
- **Non-Negotiable Principles**:
  1. **Zero-Trust towards LLMs**: Model outputs are never executable "Commands"; they are strictly untrusted "Candidate Proposals";
  2. **Host-Enforced Authorization**: Only host code executing in the non-bypassable `before_action` gate can evaluate caller identities, resource versions, and remaining budgets to construct an `AuthorizedToolCall`;
  3. **Distributed Reliability**: Through persistent distributed leases, CAS optimistic locking with monotonically increasing fencing tokens, inbox message deduplication, and transactional outboxes, the system guarantees self-healing recovery without state loss or duplicate real-world side effects.

---

## 2. Scaffold Functional Requirements (S-FR)

Tracing back to Section 1.3 (`H-FR-01` ~ `H-FR-14`) of the reference specification, the scaffold natively delivers **12 enterprise functional capabilities**:

| ID | Capability Name | Behavioral & Acceptance Specification | Traceability |
|---|---|---|---|
| **S-FR-01** | **Non-Bypassable 9-Stage Lifecycle Hooks** | Provides the core driver loop `advance(run, fencing_token)`, sequentially firing 9 interceptors: `on_run_load` → `before_context` → `before_model` → `after_model` → `before_action` → `after_action` → `before_checkpoint` → `before_finalize` → `after_finalize`. Middleware penetration or bypassing hooks to invoke tools directly is prohibited. | H-FR-01, H-FR-02 |
| **S-FR-02** | **Hexagonal Architecture & Pure Domain** | Business Agents (LA-01 ~ LA-05) reside in a pure domain layer with zero 3rd-party tech dependencies (no database drivers, HTTP clients, or vendor LLM SDKs). External interactions are abstracted as strict Ports (`ModelPort`, `PolicyPort`, `BudgetPort`, `CheckpointPort`, `EvidencePort`, `ReceiptPort`). | Spec Sec 4.1 |
| **S-FR-03** | **Process-Level Physical Isolation & Secret Proxy** | Physically decoupled into dual processes: Worker processes execute agent graphs but **never hold any API secrets**; independent Provider processes manage keys, rate limits, and egress auditing. A deterministic `FakeProvider` is provided for offline testing. | H-FR-04, H-FR-14 |
| **S-FR-04** | **Distributed Leases & Monotonic CAS Fencing** | Database-backed persistent leases control execution concurrency. Advancing state requires verifying a monotonically increasing `fencing_token`. Stale writes from zombie workers after GC pauses are blocked by CAS, preventing split-brain corruption. | H-FR-06, Spec Sec 8.3 |
| **S-FR-05** | **Idempotent Operation Keys & Unknown Reconciliation** | Before executing tools or domain mutations, a globally unique business operation key (`operation_ref`) is persisted. Network timeouts transition state to `unknown`, delegating to an exponential backoff Reconciler; blind retries of non-idempotent actions are prohibited. | H-FR-05, Spec Sec 8.7 |
| **S-FR-06** | **Protected Context Fragments & ContextManifest** | Context assembly enforces strict priority protection: system directives, student negative constraints (e.g., "no study on weekends"), and active goals have highest priority; outputs an explicit `ContextManifest` logging sources, hashes, token reservations, and truncation rationale. | H-FR-03, Spec Sec 8.4 |
| **S-FR-07** | **Tiered Memory Governance & Tombstone Deletion** | Clear separation between authoritative facts (Java), transient run working memory, conversation summaries, and confirmed personal preferences. Supports student deletion requests via tombstone markers, preventing checkpoints from reviving purged PII. | H-FR-03, Spec Sec 8.5 |
| **S-FR-08** | **Atomic Parent-Child Budget Pre-allocation & Conservation** | `BudgetPort` provides atomic reservation, allocation, settlement, and release. Delegating to leaf agents atomically carves sub-budgets from the parent budget, enforcing `sub_allocations + parent_spent <= total_approved_limit`. | H-FR-04, H-FR-08 |
| **S-FR-09** | **Infinite Loop & No-Progress Circuit Breaker** | Termination is evaluated across multiple criteria: step limits, absolute deadlines, budget exhaustion, and user cancellations. Built-in no-progress detector halts execution if input/action/argument hashes show zero state change across 3 consecutive turns. | H-FR-02, Spec Sec 8.1 |
| **S-FR-10** | **Hierarchical Multi-Agent Governance & Handoff** | Disallows chaotic group chats; enforces a fixed topology with LA-01 (Coordinator) as root and LA-02~05 as leaf roles. Standardized typed `Handoff` contract and aggregated outcomes (`completed`, `partial`, `needs_input`). | H-FR-08, Spec Sec 8.9 |
| **S-FR-11** | **Deterministic Dual-Stub Offline Ecosystem** | Built-in dual stubs: `JavaStub` simulates business context queries and receipts for Python; `AgentStub` simulates asynchronous agent responses for Java, enabling decoupled parallel development. | Master Plan I-03 |
| **S-FR-12** | **Consumer-Driven Contract Validation & DTO Generation** | Automated toolchain reading OpenAPI and JSON Schemas from `contracts/` to generate Pydantic v2 DTOs with drift detection. | Master Plan M03 |

---

## 3. Scaffold Non-Functional Requirements (S-NFR)

| ID | Category | Metric & Mandatory Constraint | Target Quality |
|---|---|---|---|
| **S-NFR-01** | **Security & Zero-Trust** | 1. **Zero Secret Leakage**: Worker processes and runtime environments never hold raw LLM API keys;<br>2. **Zero Privilege Escalation**: Host code enforces `before_action` interceptors; model prompt injections cannot bypass authorization;<br>3. **PII Sanitization**: Logs, traces, and error outputs automatically mask student PII, cookies, and bearer tokens. | Spec Sec 10.2 |
| **S-NFR-02** | **Reliability & Crash Recovery** | 1. **Idempotent Redelivery**: Re-delivering the same message 10 times results in exactly one business side effect;<br>2. **Seamless Crash Recovery**: Worker killed by SIGKILL at any step recovers cleanly from the last checkpoint upon restart;<br>3. **Split-Brain Immunity**: Stale worker state writes after lease expiration are 100% blocked by database CAS fencing. | Spec Sec 10.3 |
| **S-NFR-03** | **Determinism & Testability** | 1. **100% Deterministic Local CI**: Driven by `FakeProvider` and synthetic data, test suites pass completely offline on fresh clones;<br>2. **Sub-second Unit Tests**: Domain and rule evaluation tests execute in < 5 seconds;<br>3. **Fault Injection Ready**: Out-of-the-box support for network timeouts, concurrent CAS conflicts, budget depletion, and lease expiration fixtures. | Spec Sec 10.1 |
| **S-NFR-04** | **Performance & Concurrency Bounds** | 1. **Pure Async Non-Blocking**: End-to-end async stack (FastAPI + asyncpg + HTTPX); blocking operations are strictly forbidden on the event loop;<br>2. **Bounded Concurrency**: Maximum sub-agent recursion depth (`max_depth <= 2`) and tool concurrency are enforced by host configuration. | Spec Sec 10.4 |
| **S-NFR-05** | **Observability & Auditability** | 1. **Standard OpenTelemetry Semantics**: Correlated spans for trace, run, step, and operation;<br>2. **Non-Sampled Auditing**: Audit logs for high-risk mutations and proposals are persisted with 100% durability (sampling prohibited);<br>3. **Low-Cardinality Metrics**: Prometheus labels strictly exclude dynamic student IDs or free text. | Spec Sec 8.11, 10.5 |
| **S-NFR-06** | **Architectural Purity & Portability** | 1. **Framework Decoupling**: LangGraph serves solely as an adapter plugin; swapping the underlying graph engine does not affect domain code;<br>2. **Strict Typing**: 100% Python type hints enforced by strict Mypy verification. | Spec Sec 10.6 |

---

## 4. Service Naming & Engineering Directory Structure

Rejecting generic naming like `services/python/`, services are named according to cloud-native **Domain Capabilities**:

### 4.1 Top-Level Microservice Naming
- **`services/cogniva-learning-agent/`**: Core Agent Harness Runtime Microservice (Python, Package: `cogniva_agent`), responsible for LA-01 coordination, leaf agent execution, LangGraph orchestration, and durable state machines.
- **`services/cogniva-model-provider/`**: Isolated Model Gateway Microservice (Python, Package: `cogniva_provider`), exclusively managing API secrets, vendor SDK egress, token estimation, and usage auditing.
- **`services/cogniva-learning-core/`**: [B-Line] Java Core Business Service.
- **`services/cogniva-knowledge-service/`**: [B-Line] Java Knowledge Graph & Item Bank Service.

### 4.2 `cogniva-learning-agent` Internal Layout

```text
services/cogniva-learning-agent/
├── pyproject.toml                         # Dependency lock and tooling config (uv / pip)
├── Dockerfile                             # Unprivileged production OCI container
├── migrations/                            # Alembic runtime database migrations
│   ├── env.py
│   └── versions/
│       └── 001_agent_runtime.py           # runs, steps, checkpoints, leases, inbox, outbox
├── src/
│   └── cogniva_agent/
│       ├── domain/                        # [Pure Domain Layer] Zero external dependencies
│       │   ├── models/                    # Run, Step, Event, Session, IntentProposal
│       │   ├── coordination/              # CoordinationPlan, WorkflowCatalog, TaskHandoff
│       │   └── rules/                     # LA-01 deterministic intent rules, loop breaker
│       │
│       ├── ports/                         # [Hexagonal Ports] Abstract interface contracts
│       │   ├── model_port.py              # LLM candidate generation interface
│       │   ├── policy_port.py             # Authorization and security gate interface
│       │   ├── budget_port.py             # Atomic budget reservation interface
│       │   ├── checkpoint_port.py         # State checkpoint interface
│       │   ├── receipt_port.py            # Java business receipts and truth queries
│       │   └── evidence_port.py           # Evidence retrieval and RAG interface
│       │
│       ├── harness/                       # [Harness Core] Outer Host Control Ring
│       │   ├── kernel.py                  # advance() driver loop, CAS state machine
│       │   ├── hooks.py                   # 9-stage lifecycle hook registry & dispatcher
│       │   ├── lease.py                   # Distributed lease & monotonic fencing token check
│       │   ├── context.py                 # ContextManifest, protected fragment assembly
│       │   └── reconciler.py              # Operation status reconciler for unknown writes
│       │
│       ├── agents/                        # [Agent Implementations]
│       │   ├── la01_coordinator.py        # LA-01 Learning Coordinator Agent
│       │   ├── la02_diagnostic.py         # LA-02 Diagnostic Analysis Agent
│       │   ├── la03_explainer.py          # LA-03 Concept Explainer Agent
│       │   ├── la04_planner.py            # LA-04 Learning Path Planner Agent
│       │   └── la05_personal_advisor.py   # LA-05 Personal Suggestion Agent
│       │
│       ├── workflows/                     # [LangGraph Workflows] Deterministic graphs
│       │   ├── state.py                   # AgentState typed definition
│       │   ├── explain_flow.py            # Explain workflow graph
│       │   ├── practice_flow.py           # Practice workflow graph
│       │   └── replan_flow.py             # Replanning workflow graph
│       │
│       └── adapters/                      # [Adapters Layer] Concrete implementations
│           ├── api/                       # FastAPI internal and health check routes
│           ├── persistence/               # SQLAlchemy 2 async Core + Checkpointer
│           ├── messaging/                 # RabbitMQ / aio-pika Inbox/Outbox
│           ├── provider_client/           # HTTP/gRPC client to cogniva-model-provider
│           └── stubs/                     # Offline JavaStub and FakeClient for testing
│
└── tests/
    ├── conftest.py                        # Global fixtures & Fake environment injection
    ├── unit/                              # Domain entities, pure rules, DTO serialization
    ├── contract/                          # JSON Schema validation & negative security cases
    └── harness/                           # 9-stage hook, CAS fence conflict, 10x redelivery
```

### 4.3 `cogniva-model-provider` Internal Layout

```text
services/cogniva-model-provider/
├── pyproject.toml                         # Provider dependency config
├── Dockerfile
├── src/
│   └── cogniva_provider/
│       ├── domain/                        # ModelProfile, pricing tiers, token counters
│       ├── ports/                         # Unified vendor interface
│       ├── adapters/
│       │   ├── fake_provider.py           # Deterministic Fake generating valid JSON schemas
│       │   ├── openai_adapter.py          # OpenAI official SDK adapter
│       │   └── qwen_adapter.py            # Alibaba DashScope adapter
│       └── server/                        # Provider HTTP/gRPC proxy service
└── tests/
    ├── test_fake_provider.py
    └── test_token_accounting.py
```

---

## 5. Technology Stack & Lock Matrix (Python Maintenance Line)

| Component | Selected Stack | Rationale & Responsibility |
|---|---|---|
| **Language & Tooling** | Python 3.11+ / uv | Actively supported release line, strict reproducible locking |
| **Type System & DTO** | Pydantic v2 | High-performance runtime validation and JSON Schema serialization |
| **API Framework** | FastAPI + Uvicorn | Async ASGI microservice web framework |
| **Agent Graph Engine** | LangGraph 0.2+ | StateGraph node orchestration (contained within Adapters layer) |
| **Persistence & Migration** | SQLAlchemy 2.0+ (asyncpg) + Alembic | Fully async PostgreSQL interaction, CAS support, and migrations |
| **Messaging** | aio-pika / async AMQP | Publisher confirm and durable consumer acks |
| **Logging & Tracing** | structlog + OpenTelemetry SDK | Structured JSON logging with trace context correlation |
| **Testing** | pytest + pytest-asyncio + pytest-mock | Async/sync test runner with lightweight fault injection |

---

## 6. Implementation Evolutionary Roadmap (M03 Onward)

1. **Step 1 (Immediate Target: M03)**:
   - Establish `services/cogniva-learning-agent` and `services/cogniva-model-provider` scaffolds;
   - Configure `pyproject.toml` dependency locks and src module layouts;
   - Implement core Domain models, Ports abstractions, and `FakeProvider`;
   - Validate clean, unladen health boot and passing offline unit test suites.
2. **Step 2 (Aligned with A-01 / M06 Migration)**:
   - Complete real Alembic database migrations (runs, steps, checkpoints, leases).
3. **Step 3 (Aligned with A-02 / M12 Runtime)**:
   - Mount the LangGraph state graph onto the Harness 9-stage Hook control ring.
