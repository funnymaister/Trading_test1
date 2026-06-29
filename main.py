from contextlib import asynccontextmanager
import logging
import time

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from fastapi import FastAPI

from config import settings
from routers.market import router as market_router

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
)

app.include_router(market_router)

from config import settings
from exceptions import AppError
from logging_config import setup_logging
from routers.market import router as market_router

setup_logging()
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")
    app.state.http_client = httpx.AsyncClient(timeout=10.0)
    app.state.symbols_cache_payload = None
    app.state.symbols_cache_expires_at = 0.0
    yield
    logger.info("Shutting down application")
    await app.state.http_client.aclose()


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()
    method = request.method
    path = request.url.path

    logger.info("Request started: %s %s", method, path)

    response = await call_next(request)

    process_time = time.perf_counter() - start_time
    logger.info(
        "Request finished: %s %s -> %s in %.4fs",
        method,
        path,
        response.status_code,
        process_time,
    )

    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    logger.error("AppError on %s: %s", request.url.path, exc.message)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "path": str(request.url.path),
        },
    )


app.include_router(market_router)