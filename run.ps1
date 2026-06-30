$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not found. Create it first with: python -m venv .venv" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path ".\.env")) {
    Write-Host ".env not found. Copy .env.example to .env first." -ForegroundColor Yellow
    exit 1
}

& ".\.venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload