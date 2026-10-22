CREATE TABLE IF NOT EXISTS portfolio25.named_scenarios (
    owner_id TEXT NOT NULL, project_id TEXT NOT NULL, scenario_id TEXT NOT NULL,
    document JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(owner_id, project_id, scenario_id),
    FOREIGN KEY(owner_id, project_id) REFERENCES portfolio25.projects(owner_id, project_id)
);
