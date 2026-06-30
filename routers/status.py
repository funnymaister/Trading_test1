from fastapi import APIRouter

from core.settings import settings

router = APIRouter(tags=["status"])


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "env": settings.app_env,
        "app": settings.app_name,
    }


@router.get("/status")
async def status():
    return {
        "status": "ok",
        "env": settings.app_env,
        "app": settings.app_name,
    }