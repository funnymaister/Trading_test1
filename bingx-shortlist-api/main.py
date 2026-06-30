from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from core.security import require_internal_api_key

from core.config import get_settings
from routers.market import router as market_router
from routers.scanner import router as scanner_router
from routers.trade import router as trade_router
from services.scanner_service import start_scanner_task
from routers.status import router as status_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_scanner_task()
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.include_router(market_router)
app.include_router(trade_router)
app.include_router(scanner_router)


@app.get("/status/private")
async def private_status(_: str = Depends(require_internal_api_key)):
    return {
        "name": settings.app_name,
        "env": settings.app_env,
        "status": "ok",
        "access": "private",
    }

@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "env": settings.app_env,
        "status": "ok",
    }

@app.get("/")
async def root():
    return {
        "name": "BingX Shortlist API",
        "status": "ok",
    }

