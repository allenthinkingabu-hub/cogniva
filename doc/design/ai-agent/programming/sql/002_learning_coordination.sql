-- Reference coordination slice owned by Java learning-core.
-- Full catalog, profile, plan, budget and identity models are separate migrations.
-- Opaque references crossing domains are not foreign keys to Python-owned tables.
BEGIN;
CREATE SCHEMA learning_coordination;
CREATE TABLE learning_coordination.execution_fence (
    run_ref text PRIMARY KEY,
    holder_ref text NOT NULL,
    fencing_token bigint NOT NULL CHECK (fencing_token > 0),
    expires_at timestamptz NOT NULL,
    released boolean NOT NULL DEFAULT false,
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE learning_coordination.attempt (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    public_ref text NOT NULL UNIQUE,
    owner_ref text NOT NULL,
    goal_ref text NOT NULL,
    bundle_ref text NOT NULL,
    plan_revision_ref text NOT NULL,
    task_ref text NOT NULL,
    question_revision_ref text NOT NULL,
    scoring_revision_ref text NOT NULL,
    mode text NOT NULL CHECK (mode IN ('learning','review','diagnosis')),
    active_writer_epoch bigint NOT NULL CHECK (active_writer_epoch > 0),
    active_stream_ref text NOT NULL,
    status text NOT NULL CHECK (status IN ('open','submitted','cancelled')),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE learning_coordination.behavior_event (
    event_ref text PRIMARY KEY,
    attempt_id uuid NOT NULL REFERENCES learning_coordination.attempt(id),
    writer_epoch bigint NOT NULL CHECK (writer_epoch > 0),
    stream_ref text NOT NULL,
    seq bigint NOT NULL CHECK (seq > 0),
    event_type text NOT NULL CHECK (event_type IN ('question_viewed','option_selected','option_cleared','focus_changed')),
    option_ref text,
    focused boolean,
    monotonic_ms bigint NOT NULL CHECK (monotonic_ms >= 0),
    payload_hash text NOT NULL,
    received_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CHECK (event_type <> 'option_selected' OR option_ref IS NOT NULL),
    CHECK (event_type <> 'focus_changed' OR focused IS NOT NULL),
    UNIQUE (attempt_id, writer_epoch, stream_ref, seq)
);
CREATE TABLE learning_coordination.submission (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    public_ref text NOT NULL UNIQUE,
    attempt_id uuid NOT NULL UNIQUE REFERENCES learning_coordination.attempt(id),
    final_answer jsonb NOT NULL CHECK (jsonb_typeof(final_answer) IN ('object','array','string')),
    payload_hash text NOT NULL,
    writer_epoch bigint NOT NULL CHECK (writer_epoch > 0),
    stream_ref text NOT NULL,
    expected_last_seq bigint NOT NULL CHECK (expected_last_seq >= 0),
    submitted_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE learning_coordination.grade (
    submission_id uuid PRIMARY KEY REFERENCES learning_coordination.submission(id),
    scoring_revision_ref text NOT NULL,
    answer_revision_ref text,
    status text NOT NULL CHECK (status IN ('graded','pending_review')),
    is_correct boolean,
    result_ref text NOT NULL,
    CHECK (status <> 'graded' OR is_correct IS NOT NULL)
);
CREATE TABLE learning_coordination.behavior_snapshot (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    public_ref text NOT NULL UNIQUE,
    submission_id uuid NOT NULL REFERENCES learning_coordination.submission(id),
    revision bigint NOT NULL CHECK (revision > 0),
    quality text NOT NULL CHECK (quality IN ('received_contiguous','gaps','unavailable','conflicted')),
    frozen_event_refs jsonb NOT NULL CHECK (jsonb_typeof(frozen_event_refs) = 'array'),
    content_hash text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (submission_id, revision)
);
CREATE TABLE learning_coordination.study_cycle (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    public_ref text NOT NULL UNIQUE,
    submission_id uuid NOT NULL UNIQUE REFERENCES learning_coordination.submission(id),
    state_revision bigint NOT NULL DEFAULT 1 CHECK (state_revision > 0),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE learning_coordination.update_outcome (
    cycle_id uuid NOT NULL REFERENCES learning_coordination.study_cycle(id),
    outcome_type text NOT NULL CHECK (outcome_type IN ('learning_plan','review_plan','personal_knowledge','profile')),
    outcome_revision bigint NOT NULL DEFAULT 1 CHECK (outcome_revision > 0),
    status text NOT NULL CHECK (status IN ('pending','updated','no_change','failed','superseded')),
    input_watermark_ref text,
    reason_codes jsonb NOT NULL CHECK (jsonb_typeof(reason_codes) = 'array'),
    business_revision_ref text,
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (cycle_id, outcome_type),
    CHECK (status NOT IN ('no_change','failed','superseded') OR jsonb_array_length(reason_codes) > 0)
);
CREATE INDEX update_outcome_pending_idx ON learning_coordination.update_outcome (updated_at) WHERE status IN ('pending','failed');
CREATE TABLE learning_coordination.outcome_history (
    cycle_id uuid NOT NULL,
    outcome_type text NOT NULL,
    outcome_revision bigint NOT NULL,
    status text NOT NULL,
    reason_codes jsonb NOT NULL,
    proposal_ref text,
    payload_ref text NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (cycle_id, outcome_type, outcome_revision),
    FOREIGN KEY (cycle_id, outcome_type) REFERENCES learning_coordination.update_outcome(cycle_id, outcome_type)
);
CREATE TABLE learning_coordination.command_receipt (
    principal_ref text NOT NULL,
    operation text NOT NULL,
    goal_ref text NOT NULL,
    idempotency_key text NOT NULL,
    payload_hash text NOT NULL,
    receipt_payload jsonb NOT NULL CHECK (jsonb_typeof(receipt_payload) = 'object'),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (principal_ref, operation, goal_ref, idempotency_key)
);
CREATE TABLE learning_coordination.outbox (
    event_ref text PRIMARY KEY,
    event_type text NOT NULL,
    aggregate_ref text NOT NULL,
    aggregate_revision bigint NOT NULL CHECK (aggregate_revision > 0),
    payload_ref text NOT NULL,
    payload_hash text NOT NULL,
    correlation_ref text NOT NULL,
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','claimed','sent','unknown','dead')),
    holder_ref text,
    claim_expires_at timestamptz,
    next_attempt_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX outbox_pending_idx ON learning_coordination.outbox (next_attempt_at) WHERE status IN ('pending','claimed','unknown');
COMMIT;
