-- Reference empty-schema migration for the Python execution owner.
-- Not executed in production. LangGraph adapter tables are managed separately.
BEGIN;
CREATE SCHEMA agent_runtime;
CREATE TABLE agent_runtime.agent_run (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    public_ref text NOT NULL UNIQUE,
    create_key text NOT NULL UNIQUE,
    parent_run_ref text,
    logical_cycle_ref text,
    goal_ref text NOT NULL,
    workflow text NOT NULL CHECK (workflow IN ('bootstrap','attempt','review','assist')),
    status text NOT NULL CHECK (status IN ('queued','running','waiting_input','partial','completed','failed','cancelled','superseded')),
    state_revision bigint NOT NULL DEFAULT 1 CHECK (state_revision > 0),
    input_refs jsonb NOT NULL CHECK (jsonb_typeof(input_refs) = 'object'),
    version_manifest_ref text NOT NULL,
    authorization_ref text NOT NULL,
    deadline_at timestamptz NOT NULL,
    lease_owner text,
    lease_expires_at timestamptz,
    fencing_token bigint NOT NULL DEFAULT 0 CHECK (fencing_token >= 0),
    next_attempt_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX agent_run_pending_idx ON agent_runtime.agent_run (next_attempt_at, created_at) WHERE status IN ('queued','partial');
CREATE INDEX agent_run_goal_idx ON agent_runtime.agent_run (goal_ref, created_at);

CREATE TABLE agent_runtime.agent_inbox (
    event_id text NOT NULL,
    consumer text NOT NULL,
    payload_hash text NOT NULL,
    run_id uuid NOT NULL REFERENCES agent_runtime.agent_run(id),
    received_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (event_id, consumer)
);
CREATE TABLE agent_runtime.run_dispatch (
    run_id uuid PRIMARY KEY REFERENCES agent_runtime.agent_run(id),
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','claimed','done','failed')),
    holder_ref text,
    claim_expires_at timestamptz,
    next_attempt_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX run_dispatch_ready_idx ON agent_runtime.run_dispatch (next_attempt_at) WHERE status IN ('pending','claimed');
CREATE TABLE agent_runtime.agent_step (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id uuid NOT NULL REFERENCES agent_runtime.agent_run(id),
    logical_step text NOT NULL,
    attempt_no integer NOT NULL CHECK (attempt_no > 0),
    status text NOT NULL CHECK (status IN ('pending','running','succeeded','failed','skipped','cancelled')),
    fencing_token bigint NOT NULL CHECK (fencing_token > 0),
    input_hash text NOT NULL,
    output_ref text,
    error_code text,
    reason_code text,
    started_at timestamptz,
    finished_at timestamptz,
    UNIQUE (run_id, logical_step, attempt_no)
);
CREATE TABLE agent_runtime.run_transition (
    run_id uuid NOT NULL REFERENCES agent_runtime.agent_run(id),
    state_revision bigint NOT NULL,
    from_status text NOT NULL,
    to_status text NOT NULL,
    reason_code text NOT NULL,
    actor_ref text NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (run_id, state_revision)
);
CREATE TABLE agent_runtime.tool_call (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id uuid NOT NULL REFERENCES agent_runtime.agent_run(id),
    step_id uuid NOT NULL REFERENCES agent_runtime.agent_step(id),
    tool_name text NOT NULL,
    idempotency_key text NOT NULL,
    input_hash text NOT NULL,
    status text NOT NULL CHECK (status IN ('pending','running','succeeded','failed','unknown')),
    receipt_ref text,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (run_id, tool_name, idempotency_key)
);
CREATE TABLE agent_runtime.logical_model_call (
    run_id uuid NOT NULL REFERENCES agent_runtime.agent_run(id),
    logical_step text NOT NULL,
    logical_call_index integer NOT NULL CHECK (logical_call_index BETWEEN 1 AND 6),
    request_hash text NOT NULL,
    payload_ref text NOT NULL,
    invocation_ref text,
    execution_ref text,
    status text NOT NULL CHECK (status IN ('intent','reserved','running','succeeded','failed','unknown','cancelled')),
    result_ref text,
    usage_ref text,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (run_id, logical_step, logical_call_index)
);
CREATE TABLE agent_runtime.checkpoint_registry (
    run_id uuid NOT NULL REFERENCES agent_runtime.agent_run(id),
    epoch bigint NOT NULL CHECK (epoch > 0),
    thread_ref text NOT NULL,
    graph_version text NOT NULL,
    checkpoint_ref text NOT NULL,
    auth_revision text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (run_id, epoch)
);
CREATE TABLE agent_runtime.evidence_set (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    public_ref text NOT NULL UNIQUE,
    context_ref text NOT NULL,
    manifest_ref text NOT NULL,
    index_generation text NOT NULL,
    config_version text NOT NULL,
    passage_refs jsonb NOT NULL CHECK (jsonb_typeof(passage_refs) = 'array'),
    sufficiency text NOT NULL CHECK (sufficiency IN ('sufficient','insufficient','conflicting')),
    expires_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX evidence_set_context_idx ON agent_runtime.evidence_set (context_ref, created_at);
CREATE TABLE agent_runtime.evidence_source_link (
    evidence_set_id uuid NOT NULL REFERENCES agent_runtime.evidence_set(id),
    source_revision_ref text NOT NULL,
    passage_revision_ref text NOT NULL,
    PRIMARY KEY (evidence_set_id, passage_revision_ref)
);
CREATE INDEX evidence_source_reverse_idx ON agent_runtime.evidence_source_link (source_revision_ref);
CREATE TABLE agent_runtime.proposal_delivery (
    proposal_ref text PRIMARY KEY,
    run_id uuid NOT NULL REFERENCES agent_runtime.agent_run(id),
    logical_proposal_key text NOT NULL,
    input_hash text NOT NULL,
    payload_ref text NOT NULL,
    status text NOT NULL CHECK (status IN ('pending','sending','accepted','no_change','rejected','conflict','unknown')),
    receipt_ref text,
    next_retry_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (run_id, logical_proposal_key)
);
CREATE INDEX proposal_delivery_pending_idx ON agent_runtime.proposal_delivery (next_retry_at) WHERE status IN ('pending','sending','unknown');
COMMIT;
