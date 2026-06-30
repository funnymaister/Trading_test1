# Trading API

FastAPI backend for scanner, trade preview, trade execution, and internal status endpoints.

## Setup

\\\ash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
\\\

## Run locally

\\\ash
uvicorn main:app --reload
\\\

## Run tests

\\\ash
pytest tests -q
\\\

## Main endpoints

- GET /trade/plan
- GET /trade/preview
- POST /trade/execute
- GET /trade/positions
- POST /trade/close-position
- GET /scanner/top-movers
- POST /scanner/top-movers/refresh
- GET /status/private

## Notes

- Local secrets should go in .env
- .env is not committed; use .env.example as a template
- CI runs pytest on every push and pull request
