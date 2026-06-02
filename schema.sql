-- ============================================================
-- NEXUS HESTIA × COSMIC BUILDINGS
-- Supabase Database Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- ── STREAM CHECKS ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stream_checks (
  id               BIGSERIAL PRIMARY KEY,
  stream_id        TEXT UNIQUE NOT NULL,       -- e.g. "d1_0", "d3_4"
  stream_text      TEXT NOT NULL,              -- human-readable stream name
  domain_id        TEXT NOT NULL,              -- "d1" through "d8"
  checked          BOOLEAN DEFAULT TRUE,
  checked_by_email TEXT,
  checked_by_name  TEXT,
  completion_pct   INTEGER DEFAULT 100 CHECK (completion_pct BETWEEN 0 AND 100),
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  updated_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── AUDIT LOG ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
  id               BIGSERIAL PRIMARY KEY,
  action           TEXT NOT NULL,              -- signin, stream_checked, stream_unchecked, stream_updated, invite_sent, user_approved, user_denied, user_removed
  actor_email      TEXT,
  detail           TEXT,
  stream_id        TEXT,
  completion_pct   INTEGER,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── USERS ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id               BIGSERIAL PRIMARY KEY,
  email            TEXT UNIQUE NOT NULL,
  role             TEXT DEFAULT 'viewer' CHECK (role IN ('admin', 'viewer')),
  approved         BOOLEAN DEFAULT FALSE,
  invited_by       TEXT,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── ROW LEVEL SECURITY ────────────────────────────────────
-- Enable RLS on all tables
ALTER TABLE stream_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log     ENABLE ROW LEVEL SECURITY;
ALTER TABLE users         ENABLE ROW LEVEL SECURITY;

-- Service role (your FastAPI backend) bypasses RLS automatically.
-- These policies are for any direct Supabase client access.

-- Allow service role full access (FastAPI uses service role key)
CREATE POLICY "service_role_stream_checks" ON stream_checks
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_audit_log" ON audit_log
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_users" ON users
  FOR ALL USING (auth.role() = 'service_role');

-- ── INDEXES ───────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_stream_checks_domain   ON stream_checks(domain_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor        ON audit_log(actor_email);
CREATE INDEX IF NOT EXISTS idx_audit_log_created      ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_email            ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_approved         ON users(approved);

-- ── USEFUL VIEWS ──────────────────────────────────────────

-- Domain progress summary
CREATE OR REPLACE VIEW domain_progress AS
SELECT
  domain_id,
  COUNT(*) FILTER (WHERE checked = TRUE) AS checked_count,
  COUNT(*) AS total_checked,
  ROUND(AVG(completion_pct) FILTER (WHERE checked = TRUE), 1) AS avg_pct
FROM stream_checks
GROUP BY domain_id
ORDER BY domain_id;

-- Recent activity (last 50 events)
CREATE OR REPLACE VIEW recent_activity AS
SELECT
  action,
  actor_email,
  detail,
  stream_id,
  completion_pct,
  created_at
FROM audit_log
ORDER BY created_at DESC
LIMIT 50;

-- ── SAMPLE DATA TO VERIFY SETUP ───────────────────────────
-- INSERT INTO stream_checks (stream_id, stream_text, domain_id, checked_by_email, checked_by_name, completion_pct)
-- VALUES ('d1_0', 'Robot arm joint telemetry — position, torque, velocity', 'd1', 'natasha.bajc@nexushestia.com', 'Natasha Bajc', 100);

-- ── DONE ──────────────────────────────────────────────────
-- Tables: stream_checks, audit_log, users
-- Views:  domain_progress, recent_activity
-- ============================================================
