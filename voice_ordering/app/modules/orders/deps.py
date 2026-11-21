import os

from .hub import MonitorHub
from .menu import build_menu
from .pglog import PgEventLog
from .service import OrderingService
from .store import InMemoryStore

hub = MonitorHub()
store = InMemoryStore()
# One menu for the whole demo: SqlMenu over menu.sql when DATABASE_URL is set
# and reachable, InMemoryMenu seed otherwise (so the service always boots).
menu = build_menu()

# Postgres event log (sessions + events tables) — None when no DATABASE_URL,
# and it self-disables if Postgres goes down mid-demo. WS stays the live bus.


def _build_event_log():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return None
    try:
        return PgEventLog(dsn)
    except Exception as e:  # noqa: BLE001 - demo must boot even if PG is late
        print(f"[event-log] unavailable ({e}); continuing without persistence")
        return None


event_log = _build_event_log()
service = OrderingService(menu, store, hub, event_log=event_log)


def get_service() -> OrderingService:
    return service
