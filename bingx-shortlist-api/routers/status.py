from fastapi import APIRouter, Depends

from core.security import require_internal_api_key

router = APIRouter(prefix="/status", tags=["status"])


@router.get("/private", dependencies=[Depends(require_internal_api_key)])
async def private_status():
    return {
        "status": "ok",
        "access": "private",
    }