import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")
os.environ.setdefault("BINGX_API_KEY", "test-key")
os.environ.setdefault("BINGX_API_SECRET", "test-secret")
os.environ.setdefault("BINGX_BASE_URL", "https://open-api.bingx.com")
os.environ.setdefault("BINGX_RECV_WINDOW", "5000")
os.environ.setdefault("BINGX_TIMEOUT_SECONDS", "15")
os.environ.setdefault("SCANNER_ENABLED", "true")
os.environ.setdefault("SCANNER_INTERVAL_SECONDS", "30")
os.environ.setdefault("SCANNER_TOP_MOVERS_LIMIT", "20")

from main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def private_client():
    with TestClient(app, headers={"x-api-key": "test-internal-key"}) as c:
        yield c