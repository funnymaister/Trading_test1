from fastapi import APIRouter, Request

from core.settings import settings

router = APIRouter(tags=["status"])


@router.get("/health")
async def health(request: Request):
    return {
        "status": "ok",
        "env": settings.app_env,
        "app": settings.app_name,
    }


@router.get("/status")
async def status(request: Request):
    return {
        "status": "ok",
        "env": settings.app_env,
        "app": settings.app_name,
    }