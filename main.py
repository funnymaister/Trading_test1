import logging
import time
import uuid
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

tags_metadata = [
    {
        "name": "system",
        "description": "Health, root, and protected internal service checks.",
    },
    {
        "name": "market",
        "description": "Market shortlist and related market data endpoints.",
    },
    {
        "name": "scanner",
        "description": "Scanner refresh and top movers workflows.",
    },
    {
        "name": "trade",
        "description": "Trade planning, execution, positions, and order endpoints.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_startup env=%s app=%s", settings.app_env, settings.app_name)
    yield
    logger.info("app_shutdown env=%s app=%s", settings.app_env, settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description=(
        "FastAPI service for health checks, market shortlist workflows, "
        "scanner refresh, and protected internal operations."
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


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


app.include_router(status_router)
app.include_router(market_router)
app.include_router(scanner_router)
app.include_router(trade_router)


@app.get(
    "/",
    tags=["system"],
    summary="Root status",
    description="Returns basic application identity and environment information.",
    responses={
        200: {
            "description": "Basic application status",
            "content": {
                "application/json": {
                    "example": {
                        "name": "BingX Shortlist API",
                        "env": "prod",
                        "status": "ok",
                    }
                }
            },
        }
    },
)
@limiter.limit("30/minute")
async def root(request: Request):
    return {
        "name": settings.app_name,
        "env": settings.app_env,
        "status": "ok",
    }


@app.get(
    "/status/private",
    tags=["system"],
    summary="Private status check",
    description="Returns internal service status. Requires a valid x-api-key header.",
    responses={
        200: {
            "description": "Authorized internal status response",
            "content": {
                "application/json": {
                    "example": {
                        "name": "BingX Shortlist API",
                        "env": "prod",
                        "status": "ok",
                        "access": "private",
                    }
                }
            },
        },
        401: {
            "description": "Missing or invalid API key",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unauthorized"
                    }
                }
            },
        },
    },
)
@limiter.limit("10/minute")
async def private_status(
    request: Request,
    _: str = Depends(require_internal_api_key),
):
    return {
        "name": settings.app_name,
        "env": settings.app_env,
        "status": "ok",
        "access": "private",
    }