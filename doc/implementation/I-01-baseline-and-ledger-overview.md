# Task Specification: I-01 Baseline Audit, Scope & Execution Ledger

> **Task ID**: `I-01`  
> **Parent Work Package Ref**: `M00` (Baseline Audit, Scope & Ledger)  
> **Lane**: Lane I (Integration, Shared Baseline & Governance)  
> **Status**: Completed (`done`)  
> **Associated Design Specifications**:
> - [LA-01 Learning Coordinator Agent - Requirements & C4 Detailed Design v1.0 (Section 17 & 20)](../design/agents/LA-01-学习协调Agent-需求与C4详细设计-v1.0.md)
> - [LA-01 & Agent Harness Master Plan v1.0 (Section 12.4 & 12.7)](./LA-01与Agent-Harness-AI工程落地-Master-Plan-v1.0.md)

---

## 1. Executive Summary & Core Mission

Before any code is committed or any model endpoint is invoked, **Task I-01 serves as the immutable "Constitution and Measuring Baseline" for the Cogniva platform**. 

Cogniva (*Cognition + Nova*) is designed to help students build a self-evolving knowledge graph through continuous, adaptive learning. In this multi-lane engineering endeavor:
- **Java (B-Line)** holds the authoritative truth (grades, formal answers, student graph updates, transactions, budgets, receipts).
- **Python Harness & Multi-Agent Fleet (A-Line)** executes the durable coordinator (LA-01) and specialized leaf agents (LA-02 diagnosis, LA-03 explanation, LA-04 planning, LA-05 personal advice), communicating via proposals without direct access to authoritative databases.
- **Integration Lead (I-Line)** establishes the frozen shared contracts, baseline hashes, verification gates, and multi-lane execution ledger.

Task **I-01** guarantees that neither AI A (Python) nor AI B (Java) operates on ambiguous or silently modified specifications, providing an auditable, deterministic start line for the entire engineering lifecycle.

---

## 2. Why I-01 is the Mandatory Precursor

According to Section 12.1 and 12.7 of the Master Plan:
```
I-01 (M00 Baseline & Ledger)
  └── I-02 (M01 Toolchain & Lock)
        └── I-03 (M02 Frozen Contracts & Dual Stubs)
              └── I-04 (M03/M04/M05 Shared Scaffold & Compose)
                    └── A-01 (Python Package & Migrations) / B-01 (Java Modules)
```

Both AI A and AI B start strictly after **I-04** is delivered. In turn, I-04 requires the frozen contracts of I-03, the toolchain locks of I-02, and the baseline audit of I-01. Skipping I-01 would cause:
1. Lack of an immutable baseline fingerprint, making it impossible to detect specification drift.
2. Unclear milestone boundaries (e.g., claiming L2/L3 production readiness when only synthetic local L1 tests exist).
3. Risk of unapproved external paid API calls or unlicensed data pollution.

---

## 3. Core Activities of I-01

Task I-01 delivers 5 foundational engineering mechanisms:

### 3.1 Baseline Document Fingerprinting (`baseline-manifest.json`)
- Traverses all requirement, architecture, design, and implementation documents under `doc/`.
- Computes cryptographic SHA-256 digests and exact byte sizes for all 103 documentation files.
- Records the baseline Git commit reference (`9573764c640a215dcd01381b6876b50950c4fe92`).
- **Invariant**: Any unauthorized inline alteration to upstream specifications in future tasks will be immediately caught by hash mismatch.

### 3.2 Three-Lane Machine Execution Ledger (`task-state.json`)
- Defines the complete state machine across all 44 lane subtasks:
  - **Lane I (14 tasks)**: `I-01` to `I-14`
  - **Lane A (18 tasks)**: `A-01` to `A-16`, plus optional `A-OP01` (MCP) and `A-OP02` (Skills)
  - **Lane B (12 tasks)**: `B-01` to `B-12`
- Initial state of all subtasks is set to `todo` (with `I-01` transitioning to `done`).
- Restricts each task to its authorized paths (e.g., Lane A only modifies `services/python/` and `execution/lanes/A/`).

### 3.3 103 Requirements Traceability & Coverage Matrix (`coverage.json`)
- Systematically maps 103 items into specific parent work packages:
  - **24 FRs** (Functional Requirements: FR-01 ~ FR-24)
  - **23 NFRs** (Non-Functional Requirements: NFR-01 ~ NFR-23)
  - **28 ATs** (Acceptance Tests: AT-01 ~ AT-28)
  - **12 HRs** (Human & Governance Constraints: HR-01 ~ HR-12)
  - **16 HVs** (High-Value Scenario Validations: HV-01 ~ HV-16)
- **Invariant**: Every single requirement has assigned implementation and verification work packages; zero orphaned requirements.

### 3.4 Milestone Scope Delimitation (`scope.md`)
- Defines strict boundaries across 3 quality levels:
  - **L1 (Local Closed Loop)**: 100% deterministic, automated test suites powered by `FakeProvider` and synthetic data. No external network dependencies required.
  - **L2 (Staging Environment)**: Real provider API keys, licensed question banks, expert threshold calibrations, and Kubernetes staging cluster verification.
  - **L3 (Production Canary)**: Explicit authorization, production budget allocation, canary rollout, and SRE sign-off.

### 3.5 External Dependencies & Blockers Ledger (`external-dependencies.md`)
- Explicitly registers all external dependencies awaiting formal authorization:
  - Commercial LLM API Keys
  - Official Licensed Exam Content
  - Cloud Staging/Production Kubernetes Clusters
  - Pedagogical Expert Calibration Data
- Prohibits premature blocking: development proceeds locally at L1 without waiting for external accounts.

---

## 4. Deliverables Produced by I-01

| File Path | Description |
|---|---|
| [`execution/baseline-manifest.json`](../../execution/baseline-manifest.json) | Cryptographic digests of all 103 baseline specification documents |
| [`execution/task-state.json`](../../execution/task-state.json) | 3-lane state machine tracking 44 tasks with dependency graph |
| [`execution/coverage.json`](../../execution/coverage.json) | 103 requirement-to-task bidirectional mapping matrix |
| [`execution/scope.md`](../../execution/scope.md) | Quality milestone definitions (L1 / L2 / L3) and directory boundaries |
| [`execution/external-dependencies.md`](../../execution/external-dependencies.md) | Registry of unapproved external accounts and blocking gates |
| [`execution/evidence/I-01/attempt-1/result.json`](../../execution/evidence/I-01/attempt-1/result.json) | Structured verification test results for Task I-01 |
| [`execution/evidence/I-01/attempt-1/review.md`](../../execution/evidence/I-01/attempt-1/review.md) | Formal engineering review sign-off for I-01 |
| [`execution/handoff.md`](../../execution/handoff.md) | Operational handoff instructions for Task I-02 |

---

## 5. Bidirectional Linkage & Governance References

- **Upstream C4 & Agentic Governance Design**:
  - Refer to [LA-01-学习协调Agent-需求与C4详细设计-v1.0.md Section 20](../design/agents/LA-01-学习协调Agent-需求与C4详细设计-v1.0.md#20-企业级实施与验收基线) for the enterprise implementation baseline, E0~E4 quality gates, and LA01-HV-01~16 scenarios.
- **Upstream Multi-Agent Fleet Architecture**:
  - Refer to [学生持续学习-AI-Agent群详细设计-v1.0.md](../design/学生持续学习-AI-Agent群详细设计-v1.0.md) for domain events, OpenAPI schemas, and role profiles.
- **Downstream Master Plan Execution**:
  - Refer to [LA-01与Agent-Harness-AI工程落地-Master-Plan-v1.0.md Section 12.4](./LA-01与Agent-Harness-AI工程落地-Master-Plan-v1.0.md#124-集成验收任务线) for the exact linear progression from I-01 through I-14.
