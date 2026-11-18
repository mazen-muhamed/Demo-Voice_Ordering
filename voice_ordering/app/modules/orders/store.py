from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from .fsm import State


@dataclass
class OrderLine:
    item_id: int
    name: str
    unit_price: Decimal
    quantity: int

    @property
    def total(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass
class DtmfPress:
    digit: str
    at: datetime
    state: State
    action: str


@dataclass
class Session:
    id: str
    caller_number: str | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    state: State = State.ORDERING
    lines: dict[int, OrderLine] = field(default_factory=dict)
    dtmf_history: list[DtmfPress] = field(default_factory=list)
    dtmf_buffer: str = ""
    editing: bool = False
    confirm_expires_at: datetime | None = None

    @property
    def total(self) -> Decimal:
        return sum((l.total for l in self.lines.values()), Decimal("0"))


class InMemoryStore:
    """Demo storage. Swap with Redis/Postgres later behind the same methods."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def add(self, s: Session) -> None:
        self._sessions[s.id] = s

    def get(self, sid: str) -> Session | None:
        return self._sessions.get(sid)

    def all(self) -> list[Session]:
        return list(self._sessions.values())
