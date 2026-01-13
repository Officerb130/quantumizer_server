# Copilot instructions (quantumizer_server)

## Big picture
- Python FastAPI service lives under `app/cmd/pyapp`.
- Entrypoint is `python -m pyapp` (see `app/cmd/pyapp/__main__.py` and `app/cmd/pyapp/main.py`).
- Loads a dotenv file via `MYAPP_ENV_PATH` (recommended to set explicitly when running locally).
- Starts background services (`SyncService`, `ReportService`) and runs a single Uvicorn server hosting the Web UI + API.
  - App factory: `pyapp/api_webui.py:getApp()`
  - Binds `0.0.0.0:$PORT` where `PORT` defaults to `8199` (see `app/cmd/pyapp/util/config.py`).

## Local workflows
- From repo root:
  - `make` or `make run` (delegates into `app/cmd` and runs its default target).
- From `app/cmd`:
  - Run server: `make run`
    - Bootstraps `.venv/` (via `python -m venv`) and creates `local.env` from `local.env.example` on first run.
    - Launches with `MYAPP_ENV_PATH=./local.env python -m pyapp`.
  - Unit tests: `make unit-tests`
    - Runs pytest over `./pyapp` and writes coverage/JUnit artifacts under `app/cmd/reports/`.
  - All tests: `make tests` (currently `unit-tests` plus placeholders for integration tests).
  - Dependency maintenance: `make update-packages`
    - Updates `requirements.txt.freeze` from `requirements.txt` and is the supported way to change deps.

## Windows (Git Bash / WSL)
- Makefiles assume bash (`SHELL := /bin/bash`) and use `source`; run `make` from Git Bash or WSL.
- `app/cmd/Makefile` has Windows support for venv activation:
  - Uses `python` instead of `python3`.
  - Uses `.venv/scripts/activate` instead of `.venv/bin/activate`.

## Configuration & data
- Config is environment-variable driven via Pydantic `BaseSettings` (see `app/cmd/pyapp/util/config.py`).
- Important env vars:
  - `MYAPP_ENV_PATH`: path to dotenv file loaded by `python -m pyapp`.
  - `PORT`: Uvicorn port (default `8199`).
  - `DATA_FOLDER`: used for cache + SQLite DB location (DB path is `${DATA_FOLDER}/cache/local.db`).
  - `CLIENT_FOLDER`: used by `SyncService` for per-client data.
  - `ENABLE_SYNC_SERVICE` / `ENABLE_REPORT_SERVICE`: string flags (`"TRUE"` / `"FALSE"`).
  - `DEFAULT_LOGIN_NAME`: if set and a matching client exists, the UI can auto-login.

## Conventions when changing code
- Keep changes minimal and consistent with the existing patterns (`config.get()`, `db.get()`, FastAPI routers/templates).
- Be careful with background threads (services run concurrently with the web server).
- Prefer small, testable helpers over large inline blocks; add type hints when it improves clarity.