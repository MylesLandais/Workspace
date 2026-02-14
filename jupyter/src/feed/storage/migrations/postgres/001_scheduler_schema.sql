-- Task Scheduler Database Schema
-- PostgreSQL schema for Celery-based task scheduling with nix-shell execution
-- Migration: 001_scheduler_schema
-- Created: 2026-01-16

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Scheduled Tasks table
-- Stores task definitions with RRule-based schedules
CREATE TABLE scheduled_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) NOT NULL DEFAULT 'script',
    script_path VARCHAR(500) NOT NULL,
    nix_packages JSONB NOT NULL DEFAULT '[]'::jsonb,
    schedule_rrule TEXT NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    enabled BOOLEAN NOT NULL DEFAULT true,
    break_into_steps BOOLEAN NOT NULL DEFAULT false,
    max_concurrent INTEGER NOT NULL DEFAULT 1,
    retry_max INTEGER NOT NULL DEFAULT 3,
    retry_backoff VARCHAR(20) NOT NULL DEFAULT 'exponential',
    timeout_seconds INTEGER NOT NULL DEFAULT 7200,
    next_run_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_retry_max CHECK (retry_max >= 0 AND retry_max <= 10),
    CONSTRAINT valid_max_concurrent CHECK (max_concurrent >= 1 AND max_concurrent <= 100),
    CONSTRAINT valid_timeout CHECK (timeout_seconds >= 1 AND timeout_seconds <= 86400)
);

-- Task Runs table
-- Stores execution history for each task run
CREATE TABLE task_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES scheduled_tasks(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    exit_code INTEGER,
    stdout_log TEXT,
    stderr_log TEXT,
    error_message TEXT,
    celery_task_id VARCHAR(255),
    nix_env_hash VARCHAR(64),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'success', 'failed', 'timeout', 'cancelled'))
);

-- Task Steps table
-- For multi-step task execution tracking
CREATE TABLE task_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES task_runs(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    output_data JSONB,
    error_message TEXT,
    CONSTRAINT valid_step_status CHECK (status IN ('pending', 'running', 'success', 'failed', 'skipped'))
);

-- Nix Environments table
-- Caches pre-built nix-shell environments for fast execution
CREATE TABLE nix_environments (
    hash VARCHAR(64) PRIMARY KEY,
    packages JSONB NOT NULL,
    drv_path VARCHAR(500) NOT NULL,
    store_path VARCHAR(500),
    build_duration_ms INTEGER,
    use_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT packages_not_empty CHECK (jsonb_array_length(packages) > 0)
);

-- Indexes for performance

-- Query tasks scheduled for execution
CREATE INDEX idx_tasks_next_run ON scheduled_tasks(next_run_at)
WHERE enabled = true AND next_run_at IS NOT NULL;

-- Query tasks by status
CREATE INDEX idx_tasks_enabled ON scheduled_tasks(enabled);

-- Query task runs by task and status
CREATE INDEX idx_runs_task_status ON task_runs(task_id, status);

-- Query recent task runs
CREATE INDEX idx_runs_started_at ON task_runs(started_at DESC);

-- Query task runs by Celery task ID
CREATE INDEX idx_runs_celery_id ON task_runs(celery_task_id)
WHERE celery_task_id IS NOT NULL;

-- Query task steps by run
CREATE INDEX idx_steps_run_id ON task_steps(run_id, step_number);

-- Find frequently used nix environments
CREATE INDEX idx_nix_use_count ON nix_environments(use_count DESC);

-- Find stale nix environments for cleanup
CREATE INDEX idx_nix_last_used ON nix_environments(last_used_at);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_scheduled_tasks_updated_at
BEFORE UPDATE ON scheduled_tasks
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate task run duration
CREATE OR REPLACE FUNCTION calculate_run_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_at IS NOT NULL AND NEW.started_at IS NOT NULL THEN
        NEW.duration_ms = EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at)) * 1000;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_task_run_duration
BEFORE UPDATE OF completed_at ON task_runs
FOR EACH ROW
EXECUTE FUNCTION calculate_run_duration();

-- Function to calculate step duration
CREATE OR REPLACE FUNCTION calculate_step_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_at IS NOT NULL AND NEW.started_at IS NOT NULL THEN
        NEW.duration_ms = EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at)) * 1000;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_task_step_duration
BEFORE UPDATE OF completed_at ON task_steps
FOR EACH ROW
EXECUTE FUNCTION calculate_step_duration();

-- Views for common queries

-- Active tasks scheduled in next 24 hours
CREATE VIEW v_upcoming_tasks AS
SELECT
    id,
    name,
    task_type,
    script_path,
    schedule_rrule,
    next_run_at,
    last_run_at,
    created_at
FROM scheduled_tasks
WHERE enabled = true
    AND next_run_at IS NOT NULL
    AND next_run_at <= NOW() + INTERVAL '24 hours'
ORDER BY next_run_at ASC;

-- Recent task runs with task info
CREATE VIEW v_recent_runs AS
SELECT
    r.id AS run_id,
    r.task_id,
    t.name AS task_name,
    r.status,
    r.started_at,
    r.completed_at,
    r.duration_ms,
    r.exit_code,
    r.celery_task_id,
    r.nix_env_hash
FROM task_runs r
JOIN scheduled_tasks t ON r.task_id = t.id
ORDER BY r.started_at DESC
LIMIT 100;

-- Task execution statistics
CREATE VIEW v_task_stats AS
SELECT
    t.id AS task_id,
    t.name AS task_name,
    COUNT(r.id) AS total_runs,
    COUNT(CASE WHEN r.status = 'success' THEN 1 END) AS successful_runs,
    COUNT(CASE WHEN r.status = 'failed' THEN 1 END) AS failed_runs,
    AVG(CASE WHEN r.status = 'success' THEN r.duration_ms END) AS avg_success_duration_ms,
    MAX(r.started_at) AS last_run_at
FROM scheduled_tasks t
LEFT JOIN task_runs r ON t.id = r.task_id
GROUP BY t.id, t.name;

-- Nix environment usage statistics
CREATE VIEW v_nix_env_stats AS
SELECT
    hash,
    packages,
    use_count,
    last_used_at,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - last_used_at)) / 86400 AS days_since_used
FROM nix_environments
ORDER BY use_count DESC;

-- Comments for documentation
COMMENT ON TABLE scheduled_tasks IS 'Task definitions with RRule-based scheduling';
COMMENT ON TABLE task_runs IS 'Execution history for each task run';
COMMENT ON TABLE task_steps IS 'Multi-step task execution tracking';
COMMENT ON TABLE nix_environments IS 'Cached pre-built nix-shell environments';

COMMENT ON COLUMN scheduled_tasks.schedule_rrule IS 'RFC 5545 RRule string for recurrence';
COMMENT ON COLUMN scheduled_tasks.nix_packages IS 'JSON array of nix package names';
COMMENT ON COLUMN scheduled_tasks.retry_backoff IS 'exponential, linear, or fixed';
COMMENT ON COLUMN task_runs.nix_env_hash IS 'SHA256 hash of nix environment used';
COMMENT ON COLUMN nix_environments.drv_path IS 'Path to nix derivation (.drv) file';
