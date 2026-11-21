"""Postgres event log — makes the demo's "event log" claim real.

Every state change the session service broadcasts is ALSO appended to the
`events` table (append-only) and the `sessions` row is upserted with the
current state. Fire-and-forget: if Postgres is down, we warn once and keep
the demo running — the WS bus stays the source of truth for the live
screen; this table is the record/after-the-fact view.

Tables (also in voice_ordering/schema_events.sql). All statements are
static inline literals; data writes use parameterized queries (%s).
"""
import json
import threading
import psycopg2  


class PgEventLog:
    def __init__(self, dsn: str) -> None:

        self._dsn = dsn
        self._lock = threading.Lock()
        self._conn = None
        self._broken = False

        with self._lock, self._connection().cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS sessions (sid TEXT PRIMARY KEY, state TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now())")
            cur.execute("CREATE TABLE IF NOT EXISTS events (id BIGSERIAL PRIMARY KEY, sid TEXT NOT NULL, type TEXT NOT NULL, payload JSONB NOT NULL, ts TIMESTAMPTZ NOT NULL DEFAULT now())")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_events_sid ON events (sid)")

    def _connection(self):
        if self._conn is None or self._conn.closed:
            import psycopg2

            self._conn = psycopg2.connect(self._dsn)
            self._conn.autocommit = True
        return self._conn

    # ---------- write path (called from a worker thread) ----------
    def write(self, sid: str, state: str, type_: str, payload: dict) -> None:
        if self._broken:
            return
        try:
            with self._lock, self._connection().cursor() as cur:
                cur.execute("INSERT INTO events (sid, type, payload) VALUES (%s, %s, %s)", (sid, type_, json.dumps(payload, default=str)))
                cur.execute("INSERT INTO sessions (sid, state) VALUES (%s, %s) ON CONFLICT (sid) DO UPDATE SET state = EXCLUDED.state", (sid, state))
        except Exception as e:  # noqa: BLE001 - degrade, never break the demo
            self._broken = True
            print(f"[event-log] disabled after failure: {e}")

    def close(self) -> None:
        if self._conn and not self._conn.closed:
            self._conn.close()
