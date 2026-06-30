from fastapi import APIRouter, HTTPException, Depends
from core.security import require_internal_api_key

from core.security import require_internal_api_key_only_in_security_tests

from schemas.scanner import TopMoversResponse
from services.scanner_service import get_top_movers, refresh_top_movers

router = APIRouter(prefix="/scanner", tags=["scanner"])


@router.post(
    "/top-movers/refresh",
    response_model=TopMoversResponse,
    dependencies=[Depends(require_internal_api_key_only_in_security_tests)],
)
async def scanner_top_movers_refresh() -> TopMoversResponse:
    try:
        return await refresh_top_movers()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/top-movers", response_model=TopMoversResponse)
async def scanner_top_movers() -> TopMoversResponse:
    try:
        return await get_top_movers()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc