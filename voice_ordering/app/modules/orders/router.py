from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status

from .deps import get_service, hub
from .fsm import TERMINAL
from .schemas import (
    AddItem,
    ConfirmRequest,
    DtmfIn,
    SessionCreate,
    SessionOut,
    SetQuantity,
)
from .service import OrderingService

router = APIRouter(prefix="/api/v1", tags=["voice-ordering"])
ws_router = APIRouter()
Svc = Depends(get_service)


@router.get("/menu")
async def list_menu(svc: OrderingService = Svc):
    return [
        {"id": i.id, "name": i.name, "price": float(i.price), "aliases": i.aliases}
        for i in svc.menu.all()
    ]


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(body: SessionCreate, svc: OrderingService = Svc):
    return svc.view(await svc.create(body.caller_number, body.ttl_seconds))


@router.get("/sessions/{sid}", response_model=SessionOut)
async def get_session(sid: str, svc: OrderingService = Svc):
    return svc.view(await svc.get(sid))


@router.post("/sessions/{sid}/items", response_model=SessionOut)
async def add_item(sid: str, body: AddItem, svc: OrderingService = Svc):
    return svc.view(await svc.add_item(sid, body))


@router.patch("/sessions/{sid}/items/{item_id}", response_model=SessionOut)
async def set_quantity(sid: str, item_id: int, body: SetQuantity, svc: OrderingService = Svc):
    return svc.view(await svc.set_quantity(sid, item_id, body.quantity))


@router.delete("/sessions/{sid}/items/{item_id}", response_model=SessionOut)
async def remove_item(sid: str, item_id: int, svc: OrderingService = Svc):
    return svc.view(await svc.set_quantity(sid, item_id, 0))


@router.post("/sessions/{sid}/request-confirmation", response_model=SessionOut)
async def request_confirmation(
    sid: str, body: ConfirmRequest | None = None, svc: OrderingService = Svc
):
    ttl = body.ttl_seconds if body else 60
    return svc.view(await svc.request_confirmation(sid, ttl))


@router.post("/sessions/{sid}/confirm", response_model=SessionOut)
async def confirm(sid: str, svc: OrderingService = Svc):
    return svc.view(await svc.confirm(sid))


@router.post("/sessions/{sid}/edit", response_model=SessionOut)
async def edit(sid: str, svc: OrderingService = Svc):
    return svc.view(await svc.edit(sid))


@router.post("/sessions/{sid}/cancel", response_model=SessionOut)
async def cancel(sid: str, svc: OrderingService = Svc):
    return svc.view(await svc.cancel(sid))


@router.post("/sessions/{sid}/dtmf", response_model=SessionOut)
async def dtmf(sid: str, body: DtmfIn, svc: OrderingService = Svc):
    return svc.view(await svc.press_dtmf(sid, body.digit))


@ws_router.websocket("/ws/monitor")
async def monitor(ws: WebSocket):
    svc = get_service()
    await hub.connect(ws)
    try:
        live = [svc.view(s).model_dump(mode="json") for s in svc.store.all()
                if s.state not in TERMINAL]
        await ws.send_json({"type": "snapshot", "sessions": live})
        while True:
            await ws.receive_text()  # keep-alive; clients may ping
    except WebSocketDisconnect:
        pass
    finally:
        hub.disconnect(ws)
