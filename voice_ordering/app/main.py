import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.modules.orders.deps import service
from app.modules.orders.errors import DomainError
from app.modules.orders.router import router, ws_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    async def sweeper():
        while True:
            await asyncio.sleep(5)
            await service.sweep_expired()

    task = asyncio.create_task(sweeper())
    yield
    task.cancel()


app = FastAPI(title="Voice Ordering Demo", lifespan=lifespan)
app.include_router(router)
app.include_router(ws_router)


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
