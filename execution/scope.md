# Cogniva Platform Scope & Milestone Boundaries

## 1. Project Overview & Architecture
Cogniva (Cognition + Nova) is a general-purpose agentic learning and examination platform. It empowers students to construct their own structured knowledge graphs through continuous, adaptive learning and feedback.

### Key Architectural Boundaries
- **Java Platform (B-Line)**: Holds the authoritative truth. Responsible for user authentication, question bank & knowledge graph versioning, submissions, authoritative grading, formal personal profile/graph updates, subscriptions, budgets, and idempotent receipts.
- **Python Harness & Multi-Agent Fleet (A-Line)**: Responsible for the durable agent execution runtime (RunController, Checkpoint/LangGraph adapter), LA-01 coordinator, and specialized leaf agents (LA-02 diagnosis, LA-03 explanation, LA-04 planning, LA-05 personal advice). Communicates via proposals and receipts; never writes directly to Java authoritative tables.
- **Integration & Governance (I-Line)**: Owns contracts (`contracts/`), shared scaffolding, root build automation (`Makefile`), local infrastructure (`infra/local`), and milestone gates (L1, L2, L3).

---

## 2. Milestone Boundaries

### Level 1 (L1) Milestone: Local Reproducible Loop (Gate: I-09 / M30)
- **Scope**: Complete end-to-end user journeys (exploration, diagnostic assessment, concept explanation, practice, and replanning) running deterministically on a local clean clone.
- **Model Boundary**: Driven by `FakeProvider` and deterministic contract test fixtures. Real external LLM calls are mocked/simulated to ensure 100% reproducible test suites.
- **Data Boundary**: Synthetic knowledge nodes, prerequisite graphs, and authorized demo question items.
- **Exit Criteria**: All unit, contract, and integration tests pass cleanly; zero manual mocks in place of business logic; reproducible via `make verify` and local containers.

### Level 2 (L2) Milestone: Staging & Real Infrastructure (Gate: I-12 / M33)
- **Scope**: Deployment to Kubernetes staging cluster (`infra/k8s/overlays/stage`).
- **Model Boundary**: Real external provider API keys approved under strict budget and destination security policies.
- **Data Boundary**: Licensed question bank content, expert threshold evaluation, and staging database migration/rollback verification.
- **Exit Criteria**: Real model accuracy/cost metrics evaluated; recovery and disaster drill (RPO <= 5m, RTO <= 60m) confirmed; security audits clean.

### Level 3 (L3) Milestone: Production Canary & Governance (Gate: I-14 / M35)
- **Scope**: Production deployment with canary release, observability dashboard sign-off, and business SLA validation.
- **Prerequisites**: Explicit management authorization, production budget pre-allocation, and SRE/Security sign-offs.

---

## 3. Work Breakdown & Directory Ownership

| Lane | ID Range | Target Directory | Responsibilities |
|---|---|---|---|
| **Lane I (Integration)** | I-01 ~ I-14 | `contracts/`, `infra/`, `pipelines/`, `scripts/`, `execution/`, `Makefile` | Contract freeze, shared tooling, local Compose, CI pipelines, and cross-lane gates |
| **Lane A (Python)** | A-01 ~ A-16, A-OP01/02 | `services/python/`, `execution/lanes/A/` | Agent Harness, LA-01~05, Provider boundary, RAG retrieval, execution migrations |
| **Lane B (Java)** | B-01 ~ B-12 | `services/java/`, `apps/student-web/`, `execution/lanes/B/` | Core business services, authorization, submissions, receipts, Web UI |

---

## 4. Invariant Rules
1. No task is marked `done` without automated verification passing and execution evidence recorded.
2. Code in Lane A and Lane B must not modify shared files or cross-lane boundaries without formal contract change requests.
3. No credentials, secret keys, or unapproved network destinations are allowed in source control.
