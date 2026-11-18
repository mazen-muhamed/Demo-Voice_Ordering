from enum import Enum


class State(str, Enum):
    ORDERING = "ORDERING"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


TERMINAL = {State.CONFIRMED, State.CANCELLED, State.EXPIRED}

TRANSITIONS: dict[State, set[State]] = {
    State.ORDERING: {State.PENDING_CONFIRMATION, State.CANCELLED, State.EXPIRED},
    State.PENDING_CONFIRMATION: {
        State.CONFIRMED,
        State.ORDERING,  # caller wants to edit
        State.CANCELLED,
        State.EXPIRED,
    },
    State.CONFIRMED: set(),
    State.CANCELLED: set(),
    State.EXPIRED: set(),
}


def can_transition(src: State, dst: State) -> bool:
    return dst in TRANSITIONS[src]
