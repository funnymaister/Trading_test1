# Trading API

FastAPI backend for scanner, trade preview, trade execution, and internal status endpoints.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run locally

```bash
uvicorn main:app --reload
```

## Run tests

```bash
pytest tests -q
```

## Main endpoints

- `GET /trade/plan`
- `GET /trade/preview`
- `POST /trade/execute`
- `GET /trade/positions`
- `POST /trade/close-position`
- `GET /scanner/top-movers`
- `POST /scanner/top-movers/refresh`
- `GET /status/private`

## Notes

- Local secrets should go in `.env`
- `.env` is not committed; use `.env.example` as a template
- CI runs pytest on every push and pull request


## Post-deploy checklist

Use this checklist after every deploy to Render.

- [ ] Confirm the deploy finished successfully and the service status is `Live`.
- [ ] Open `/health` and verify it returns the expected JSON response.
- [ ] Open `/status` and verify the app responds correctly.
- [ ] Call `/status/private` without `x-api-key` and confirm it returns `401 Unauthorized`.
- [ ] Call `/status/private` with a valid `x-api-key` and confirm it returns `200 OK`.
- [ ] Check one main business endpoint, for example `/market/shortlist`.
- [ ] Open Render **Logs** and confirm `app_startup` appears without traceback errors.
- [ ] If environment variables were changed, verify the new values are active after redeploy.
- [ ] Open Render **Metrics** and check for unusual CPU, memory, or traffic spikes.
- [ ] Run `git status` locally and confirm the working tree is clean.
- [ ] Verify `.env`, secrets, and `__pycache__` are not being committed.