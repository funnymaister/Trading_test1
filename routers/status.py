from fastapi import APIRouter, Request

from core.settings import settings

router = APIRouter(tags=["system"])


@router.get(
    "/health",
    summary="Health check",
    description="Returns a lightweight health response for uptime checks and deployment verification.",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "env": "prod",
                        "app": "BingX Shortlist API",
                    }
                }
            },
        }
    },
)
async def health(request: Request):
    return {
        "status": "ok",
        "env": settings.app_env,
        "app": settings.app_name,
    }


@router.get(
    "/status",
    summary="Public service status",
    description="Returns public application status information for quick runtime verification.",
    responses={
        200: {
            "description": "Public service status",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "env": "prod",
                        "app": "BingX Shortlist API",
                    }
                }
            },
        }
    },
)
async def status(request: Request):
    return {
        "status": "ok",
        "env": settings.app_env,
        "app": settings.app_name,
    }