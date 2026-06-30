import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from core.limiter import limiter
from core.logging_config import setup_logging
from core.security import require_internal_api_key
from core.settings import settings
from routers.market import router as market_router
from routers.scanner import router as scanner_router
from routers.status import router as status_router
from routers.trade import router as trade_router

setup_logging(settings.log_level)
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_startup env=%s app=%s", settings.app_env, settings.app_name)
    yield
    logger.info("app_shutdown env=%s app=%s", settings.app_env, settings.app_name)


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(status_router)
app.include_router(market_router)
app.include_router(scanner_router)
app.include_router(trade_router)


@app.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    return {
        "name": settings.app_name,
        "env": settings.app_env,
        "status": "ok",
    }


@app.get("/status/private")
@limiter.limit("10/minute")
async def private_status(request: Request, _: str = Depends(require_internal_api_key)):
    return {
        "name": settings.app_name,
        "env": settings.app_env,
        "status": "ok",
        "access": "private",
    }