# External Dependencies & Authorization Ledger

This document registers all third-party, commercial, infrastructure, and expert dependencies that require external approval or provisioned credentials.

According to Master Plan Section 1.3 & 12.7, **local development and L1 milestone must proceed without external unapproved credentials using deterministic fakes and synthetic content**. No task shall stall waiting for external resources until their corresponding gate tasks (I-10, I-11, I-14).

---

## 1. External Credentials & Paid APIs

| Dependency ID | Description | Required At | Current Status | L1 Local Fallback Strategy |
|---|---|---|---|---|
| `EXT-DEP-01` | Commercial LLM API Keys (e.g. OpenAI / Anthropic / Qwen) | `I-10` (M31) | **Awaiting Approval** | `FakeProvider` returning deterministic JSON responses matching schemas |
| `EXT-DEP-02` | Licensed Examination Question Bank & Copyrighted Material | `I-10` (M31) | **Awaiting Audit** | Synthetic knowledge nodes and synthetic multi-choice items |
| `EXT-DEP-03` | Staging Kubernetes Infrastructure & Managed Services (RDS/RabbitMQ) | `I-11` (M32) | **Awaiting Provisioning** | Local Docker Compose environment (`infra/local/docker-compose.yml`) |
| `EXT-DEP-04` | Pedagogical Expert Thresholds & Mastery Calibration Data | `I-10` (M31) | **Awaiting Review** | Conservative rule-based baseline without pseudo-probabilities |
| `EXT-DEP-05` | Production Deployment & Canary Release Authorization | `I-14` (M35) | **Awaiting Authorization** | Local/Stage delivery package verification |

---

## 2. Security & Compliance Constraints
- **Zero Secrets in Git**: No real API keys, bearer tokens, or internal database passwords shall be committed.
- **Provider Boundary**: When real LLM keys are eventually provisioned, they must remain exclusively within the isolated `services/python/provider/` service. General worker processes shall not hold raw API keys.
- **Audit Logs**: All external calls must log caller identity, token count, cost estimation, and destination endpoint without leaking prompt payloads or student PII.
