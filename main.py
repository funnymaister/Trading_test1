import logging
import time
import uuid

from fastapi import FastAPI, Request

from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()

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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.perf_counter()

    logger.info(
        "request_started request_id=%s method=%s path=%s client=%s",
        request_id,
        request.method,
        request.url.path,
        request.client.host if request.client else "unknown",
    )

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_failed request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        raise

    process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

    logger.info(
        "request_completed request_id=%s method=%s path=%s status_code=%s duration_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        process_time_ms,
    )

    response.headers["X-Request-ID"] = request_id
    return response


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