import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable

from .errors import (
    InvalidOrder,
    InvalidTransition,
    ItemNotFound,
    SessionExpired,
    SessionNotFound,
)
from .fsm import TERMINAL, State, can_transition
from .hub import MonitorHub
from .menu import MenuItem, MenuProvider
from .schemas import AddItem, SessionOut
from .store import DtmfPress, InMemoryStore, OrderLine, Session

MAX_LINE_QTY = 50
_EDIT_RE = re.compile(r"^(\d+)\*(\d+)$")  # "<item index>*<quantity>"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OrderingService:
    def __init__(
        self,
        menu: MenuProvider,
        store: InMemoryStore,
        hub: MonitorHub,
        now: Callable[[], datetime] = _utcnow,
    ) -> None:
        self.menu, self.store, self.hub, self._now = menu, store, hub, now

    # ---------- helpers ----------
    def view(self, s: Session) -> SessionOut:
        return SessionOut.from_session(s, self._now())

    async def _emit(self, type_: str, s: Session, **extra) -> None:
        await self.hub.broadcast(
            {"type": type_, "session": self.view(s).model_dump(mode="json"), **extra}
        )

    def _touch(self, s: Session) -> None:
        s.updated_at = self._now()

    def _expire_if_due(self, s: Session) -> bool:
        if s.state in TERMINAL:
            return False
        now = self._now()
        pending_due = (
            s.state == State.PENDING_CONFIRMATION
            and s.confirm_expires_at is not None
            and now >= s.confirm_expires_at
        )
        if now >= s.expires_at or pending_due:
            s.state, s.editing, s.updated_at = State.EXPIRED, False, now
            return True
        return False

    def _transition(self, s: Session, new: State) -> None:
        if not can_transition(s.state, new):
            raise InvalidTransition(f"cannot go from {s.state.value} to {new.value}")
        s.state = new
        self._touch(s)

    async def get(self, sid: str) -> Session:
        s = self.store.get(sid)
        if s is None:
            raise SessionNotFound("session not found")
        if self._expire_if_due(s):
            await self._emit("session_expired", s)
        return s

    async def _active(self, sid: str) -> Session:
        s = await self.get(sid)
        if s.state == State.EXPIRED:
            raise SessionExpired("session expired")
        if s.state in TERMINAL:
            raise InvalidTransition(f"session is already {s.state.value}")
        return s

    async def _editable(self, sid: str) -> Session:
        s = await self._active(sid)
        if s.state != State.ORDERING:
            raise InvalidTransition(
                f"items can't change in {s.state.value}; call /edit first"
            )
        return s

    def _resolve(self, body: AddItem) -> MenuItem:
        item = (
            self.menu.get(body.item_id)
            if body.item_id is not None
            else self.menu.find(body.name or "")
        )
        if item is None:
            raise ItemNotFound("item not found in menu")
        return item

    # ---------- session ----------
    async def create(self, caller_number: str | None, ttl_seconds: int) -> Session:
        now = self._now()
        s = Session(
            id=str(uuid.uuid4()),
            caller_number=caller_number,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
        self.store.add(s)
        await self._emit("session_created", s)
        return s

    # ---------- items ----------
    async def add_item(self, sid: str, body: AddItem) -> Session:
        s = await self._editable(sid)
        item = self._resolve(body)
        line = s.lines.get(item.id)
        new_qty = (line.quantity if line else 0) + body.quantity
        if new_qty > MAX_LINE_QTY:
            raise InvalidOrder(f"max quantity per item is {MAX_LINE_QTY}")
        if line:
            line.quantity = new_qty
        else:
            s.lines[item.id] = OrderLine(item.id, item.name, item.price, new_qty)
        self._touch(s)
        await self._emit("item_added", s, item_id=item.id)
        return s

    async def set_quantity(self, sid: str, item_id: int, qty: int) -> Session:
        s = await self._editable(sid)
        if item_id not in s.lines:
            raise ItemNotFound("item not in this order")
        if qty == 0:
            del s.lines[item_id]
            event = "item_removed"
        else:
            s.lines[item_id].quantity = qty
            event = "item_updated"
        self._touch(s)
        await self._emit(event, s, item_id=item_id)
        return s

    # ---------- state transitions ----------
    async def request_confirmation(self, sid: str, ttl_seconds: int = 60) -> Session:
        s = await self._active(sid)
        if not s.lines:
            raise InvalidOrder("cannot confirm an empty order")
        self._transition(s, State.PENDING_CONFIRMATION)
        s.editing, s.dtmf_buffer = False, ""
        s.confirm_expires_at = self._now() + timedelta(seconds=ttl_seconds)
        await self._emit("state_changed", s)
        return s

    async def confirm(self, sid: str) -> Session:
        s = await self._active(sid)
        self._transition(s, State.CONFIRMED)
        s.confirm_expires_at = None
        await self._emit("state_changed", s)
        return s

    async def edit(self, sid: str, editing_mode: bool = False) -> Session:
        s = await self._active(sid)
        self._transition(s, State.ORDERING)
        s.confirm_expires_at, s.editing, s.dtmf_buffer = None, editing_mode, ""
        await self._emit("state_changed", s)
        return s

    async def cancel(self, sid: str) -> Session:
        s = await self._active(sid)
        self._transition(s, State.CANCELLED)
        s.editing, s.confirm_expires_at = False, None
        await self._emit("state_changed", s)
        return s

    # ---------- DTMF ----------
    async def press_dtmf(self, sid: str, digit: str) -> Session:
        """ORDERING: 1=ask confirmation, 0=cancel.
        PENDING_CONFIRMATION: 1=confirm, 2=edit, 0=cancel.
        Edit mode: digits build '<index>*<qty>', '#' applies it (qty 0 removes);
        '#' on an empty buffer = done editing -> back to confirmation.
        Every press is saved in dtmf_history.
        """
        s = await self._active(sid)
        state_at_press, action = s.state, "ignored"

        if s.state == State.PENDING_CONFIRMATION:
            if digit == "1":
                await self.confirm(sid)
                action = "confirm"
            elif digit == "2":
                await self.edit(sid, editing_mode=True)
                action = "edit"
            elif digit == "0":
                await self.cancel(sid)
                action = "cancel"
        elif s.editing:
            action = await self._edit_digit(s, digit)
        else:
            if digit == "1" and s.lines:
                await self.request_confirmation(sid)
                action = "request_confirmation"
            elif digit == "0":
                await self.cancel(sid)
                action = "cancel"

        s.dtmf_history.append(DtmfPress(digit, self._now(), state_at_press, action))
        self._touch(s)
        await self._emit("dtmf", s, digit=digit, action=action)
        return s

    async def _edit_digit(self, s: Session, digit: str) -> str:
        if digit != "#":
            s.dtmf_buffer += digit
            return "buffer"
        buf, s.dtmf_buffer = s.dtmf_buffer, ""
        if not buf:
            if not s.lines:
                return "edit_invalid"
            await self.request_confirmation(s.id)
            return "request_confirmation"
        m = _EDIT_RE.match(buf)
        lines = list(s.lines.values())
        if not m or not (1 <= int(m[1]) <= len(lines)):
            return "edit_invalid"
        line, qty = lines[int(m[1]) - 1], int(m[2])
        if qty > MAX_LINE_QTY:
            return "edit_invalid"
        if qty == 0:
            del s.lines[line.item_id]
        else:
            line.quantity = qty
        return "edit_applied"

    # ---------- background ----------
    async def sweep_expired(self) -> None:
        for s in self.store.all():
            if self._expire_if_due(s):
                await self._emit("session_expired", s)
