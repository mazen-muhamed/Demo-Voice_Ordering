

CREATE TABLE IF NOT EXISTS sessions (
    sid        TEXT PRIMARY KEY,
    state      TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS events (
    id      BIGSERIAL PRIMARY KEY,
    sid     TEXT NOT NULL,
    type    TEXT NOT NULL,
    payload JSONB NOT NULL,
    ts      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_events_sid ON events (sid);
