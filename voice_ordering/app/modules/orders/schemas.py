from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from .fsm import State
from .store import Session


def _money(v: Decimal) -> float:
    return float(v.quantize(Decimal("0.01")))


class SessionCreate(BaseModel):
    caller_number: str | None = None
    ttl_seconds: int = Field(300, ge=30, le=3600)


class AddItem(BaseModel):
    item_id: int | None = None
    name: str | None = Field(None, min_length=1)
    quantity: int = Field(1, ge=1, le=50)

    @model_validator(mode="after")
    def _exactly_one(self):
        if (self.item_id is None) == (self.name is None):
            raise ValueError("provide exactly one of item_id or name")
        return self


class SetQuantity(BaseModel):
    quantity: int = Field(ge=0, le=50)  # 0 removes the line


class ConfirmRequest(BaseModel):
    ttl_seconds: int = Field(60, ge=5, le=600)


class DtmfIn(BaseModel):
    digit: str = Field(pattern=r"^[0-9*#]$")


class LineOut(BaseModel):
    item_id: int
    name: str
    unit_price: float
    quantity: int
    line_total: float


class DtmfOut(BaseModel):
    digit: str
    at: datetime
    state: State
    action: str


class SessionOut(BaseModel):
    id: str
    caller_number: str | None
    state: State
    items: list[LineOut]
    total: float
    editing: bool
    dtmf_buffer: str
    dtmf_history: list[DtmfOut]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    expires_in_seconds: int
    confirmation_expires_at: datetime | None
    confirmation_expires_in_seconds: int | None

    @classmethod
    def from_session(cls, s: Session, now: datetime) -> "SessionOut":
        def left(t: datetime) -> int:
            return max(0, int((t - now).total_seconds()))

        live = s.state in (State.ORDERING, State.PENDING_CONFIRMATION)
        pending = s.state == State.PENDING_CONFIRMATION and s.confirm_expires_at
        return cls(
            id=s.id,
            caller_number=s.caller_number,
            state=s.state,
            items=[
                LineOut(
                    item_id=l.item_id,
                    name=l.name,
                    unit_price=_money(l.unit_price),
                    quantity=l.quantity,
                    line_total=_money(l.total),
                )
                for l in s.lines.values()
            ],
            total=_money(s.total),
            editing=s.editing,
            dtmf_buffer=s.dtmf_buffer,
            dtmf_history=[
                DtmfOut(digit=p.digit, at=p.at, state=p.state, action=p.action)
                for p in s.dtmf_history
            ],
            created_at=s.created_at,
            updated_at=s.updated_at,
            expires_at=s.expires_at,
            expires_in_seconds=left(s.expires_at) if live else 0,
            confirmation_expires_at=s.confirm_expires_at if pending else None,
            confirmation_expires_in_seconds=left(s.confirm_expires_at) if pending else None,
        )
