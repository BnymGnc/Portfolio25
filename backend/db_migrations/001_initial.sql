CREATE TABLE IF NOT EXISTS portfolio25.users (
    id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
    onboarding_version INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS portfolio25.sessions (
    digest TEXT PRIMARY KEY, user_id TEXT REFERENCES portfolio25.users(id),
    csrf TEXT NOT NULL, expires DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_expiry_idx ON portfolio25.sessions(expires);
CREATE TABLE IF NOT EXISTS portfolio25.attempts (bucket TEXT NOT NULL, moment DOUBLE PRECISION NOT NULL);
CREATE INDEX IF NOT EXISTS attempts_bucket_time_idx ON portfolio25.attempts(bucket, moment);
CREATE TABLE IF NOT EXISTS portfolio25.projects (
    owner_id TEXT NOT NULL REFERENCES portfolio25.users(id), project_id TEXT NOT NULL,
    revision BIGINT NOT NULL CHECK(revision > 0), document JSONB NOT NULL,
    latest_calculation_id TEXT,
    PRIMARY KEY(owner_id, project_id),
    CHECK(document->>'id' = project_id),
    CHECK((document->>'revision')::BIGINT = revision)
);
CREATE TABLE IF NOT EXISTS portfolio25.calculations (
    owner_id TEXT NOT NULL, project_id TEXT NOT NULL, calculation_id TEXT NOT NULL,
    document JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(owner_id, project_id, calculation_id),
    FOREIGN KEY(owner_id, project_id) REFERENCES portfolio25.projects(owner_id, project_id)
);
CREATE TABLE IF NOT EXISTS portfolio25.legacy_imports (
    source_digest TEXT PRIMARY KEY, imported_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
