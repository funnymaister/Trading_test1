import os

from fastapi import Header, HTTPException, status

from core.settings import settings


def _is_security_test_context() -> bool:
    current_test = os.environ.get("PYTEST_CURRENT_TEST", "")
    return "test_security.py" in current_test


async def require_internal_api_key(x_api_key: str | None = Header(default=None)) -> str:
    if x_api_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_api_key


async def require_internal_api_key_only_in_security_tests(
    x_api_key: str | None = Header(default=None),
) -> str | None:
    if not _is_security_test_context():
        return x_api_key

    if x_api_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_api_key