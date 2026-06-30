# test-change

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from core.security import require_internal_api_key
from core.settings import settings
from routers.market import router as market_router
from routers.status import router as status_router

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")
    yield
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.include_router(status_router)
app.include_router(market_router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "env": settings.app_env,
        "status": "ok",
    }


@app.get("/status/private")
async def private_status(_: str = Depends(require_internal_api_key)):
    return {
        "name": settings.app_name,
        "env": settings.app_env,
        "status": "ok",
        "access": "private",
    }