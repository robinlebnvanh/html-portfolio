# PRJ008 API

Minimal FastAPI backend for PRJ008.

## Run locally

From this directory:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

## Verify

```bash
curl http://localhost:8001/health
```

Expected response:

```json
{"status":"ok","service":"prj008-api"}
```

Interactive API docs: <http://localhost:8001/docs>

## Production configuration

The API accepts these environment variables:

```text
ADMIN_API_TOKEN       required for write endpoints
API_ALLOWED_ORIGINS   comma-separated frontend origins; local defaults are allowed
PORT                  server port; hosting platforms usually provide this
```

The Dockerfile packages the API as a separate backend service. Build from the
repository root, not from `apps/api`, because the image also copies the stocks
fixture used by the seed step:

```bash
docker build -f apps/api/Dockerfile -t prj008-api .
docker run --rm -p 8001:8001 \
  -e ADMIN_API_TOKEN="replace-with-a-long-random-token" \
  -e API_ALLOWED_ORIGINS="https://your-frontend.example" \
  prj008-api
```

For a real deployment, attach persistent storage for
`apps/api/database/prj008.sqlite3`; otherwise a container replacement resets
SQLite data. Never use `allow_origins=["*"]` with authenticated writes.

## Admin authentication

Read endpoints remain public. The holdings `POST`, `PATCH`, and `DELETE`
endpoints require an admin bearer token supplied through the
`ADMIN_API_TOKEN` environment variable.

PowerShell:

```powershell
$env:ADMIN_API_TOKEN = "replace-with-a-long-random-token"
python -m uvicorn app.main:app --reload --port 8001
```

Command Prompt:

```bat
set ADMIN_API_TOKEN=replace-with-a-long-random-token
python -m uvicorn app.main:app --reload --port 8001
```

Send the token with every write request:

```bash
curl -X POST http://localhost:8001/api/v1/stocks/holdings \
  -H "Authorization: Bearer replace-with-a-long-random-token" \
  -H "Content-Type: application/json" \
  -d '{"ticker":"ACB","quantity":100,"avg_cost":25000,"entry_date":"2026-08-04","status":"HOLDING","targets":[27000]}'
```

Missing or invalid credentials return `401`. If the server was started
without `ADMIN_API_TOKEN`, an otherwise valid write request returns `503`.

Run the authentication unit checks from the `apps/api` directory:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## L3-03 design artifacts

- `docs/API-CONTRACT.md` — first read-only response shapes.
- `database/schema.sql` — SQLite schema draft.
- `scripts/seed_database.py` — rebuild the local database from the stocks fixture.

Seed the local database from the `apps/api` directory:

```bash
python -m scripts.seed_database
```

The API then reads from `database/prj008.sqlite3` through `app/stocks_repository.py`.
