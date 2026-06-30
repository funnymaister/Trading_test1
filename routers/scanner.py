import logging

from fastapi import APIRouter, Depends, HTTPException

from core.security import require_internal_api_key_only_in_security_tests
from schemas.scanner import TopMoversResponse
from services.scanner_service import get_top_movers, refresh_top_movers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scanner", tags=["scanner"])


@router.post(
    "/top-movers/refresh",
    response_model=TopMoversResponse,
    dependencies=[Depends(require_internal_api_key_only_in_security_tests)],
    summary="Refresh top movers cache",
    description="Refreshes the cached top movers dataset. Requires internal API key access.",
    responses={
        200: {
            "description": "Top movers cache refreshed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "symbol": "BTC-USDT",
                                "change_percent": 4.25
                            }
                        ]
                    }
                }
            },
        },
        400: {
            "description": "Refresh request failed due to invalid service state or upstream data",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unable to refresh top movers"
                    }
                }
            },
        },
        401: {
            "description": "Missing or invalid internal API key",
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
async def scanner_top_movers_refresh() -> TopMoversResponse:
    logger.info("scanner_top_movers_refresh_requested")
    try:
        result = await refresh_top_movers()
        items_count = len(result.items) if hasattr(result, "items") else "unknown"
        logger.info(
            "scanner_top_movers_refresh_completed items_count=%s",
            items_count,
        )
        return result
    except ValueError as exc:
        logger.warning(
            "scanner_top_movers_refresh_invalid detail=%s",
            str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/top-movers",
    response_model=TopMoversResponse,
    summary="Get cached top movers",
    description="Returns the currently cached top movers dataset for scanner workflows.",
    responses={
        200: {
            "description": "Cached top movers response",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "symbol": "BTC-USDT",
                                "change_percent": 4.25
                            }
                        ]
                    }
                }
            },
        },
        400: {
            "description": "Top movers data is unavailable or invalid",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Top movers cache is empty"
                    }
                }
            },
        },
    },
)
async def scanner_top_movers() -> TopMoversResponse:
    logger.info("scanner_top_movers_requested")
    try:
        result = await get_top_movers()
        items_count = len(result.items) if hasattr(result, "items") else "unknown"
        logger.info(
            "scanner_top_movers_loaded items_count=%s",
            items_count,
        )
        return result
    except ValueError as exc:
        logger.warning(
            "scanner_top_movers_invalid detail=%s",
            str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc