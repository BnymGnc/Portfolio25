CREATE TABLE IF NOT EXISTS portfolio25.building_intakes (
 owner_id TEXT NOT NULL REFERENCES portfolio25.users(id), intake_id TEXT NOT NULL,
 revision BIGINT NOT NULL CHECK(revision>0), document JSONB NOT NULL,
 PRIMARY KEY(owner_id,intake_id)
);
