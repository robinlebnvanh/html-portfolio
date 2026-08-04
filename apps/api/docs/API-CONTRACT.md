# PRJ008 API Contract

## Scope

L3-03 defines the first read-only data contract before database access is implemented.

Base URL during local development:

```text
http://localhost:8001
```

The frontend reads its API base URL from `apps/stocks-app/assets/js/config.js`.
Change that one value for a deployed backend; do not scatter production URLs
through individual HTML files. The backend reads allowed browser origins from
`API_ALLOWED_ORIGINS` (comma-separated) and defaults to the two local origins.

The API uses `snake_case`, ISO dates (`YYYY-MM-DD`), integer VND prices, and numeric percentages where the source data is numeric. This keeps the backend contract independent from the current display strings in the static frontend fixture.

## GET `/api/v1/stocks/portfolio`

Returns the current portfolio summary, holdings, and watchlist. Holdings
include their stable numeric `id`, which the Admin UI uses for PATCH/DELETE.

```json
{
  "updated": "2026-06-18",
  "holdings": [
    {
      "id": 1,
      "ticker": "VIC",
      "quantity": 100,
      "avg_cost": 192000,
      "entry_date": "2026-06-18",
      "stop_loss": 186000,
      "targets": [210000, 219900, 237700],
      "status": "HOLDING",
      "note": "Position trade. Chờ MACD crossover lên xác nhận."
    }
  ],
  "watchlist": ["ACB", "VRE", "VTP"],
  "summary": {
    "total_invested": 21855000,
    "positions": 2,
    "note": "Cập nhật portfolio.json mỗi khi mua/bán/update SL/TP"
  }
}
```

## GET `/api/v1/stocks/journals`

Returns journal data keyed by ticker.

```json
{
  "VIC": {
    "ticker": "VIC",
    "snapshots": [
      {
        "date": "2026-06-18",
        "price": 203500,
        "change_percent": 5.99,
        "rsi": 43.3,
        "macd": "-2.88 < -1.75 (bear)",
        "score": "+2",
        "recommendation": "🔶 TÍCH LŨY",
        "note": "Cú bật mạnh +6%, StochRSI=100, vol 1.08x"
      }
    ],
    "trades": [
      {
        "date": "2026-06-18",
        "type": "MUA",
        "price": 192000,
        "stop_loss": null,
        "pnl": "Giá vốn ban đầu",
        "note": ""
      }
    ],
    "entry_plan": [
      {
        "condition": "🛡️ Stop-loss cứng",
        "entry_text": "**186,000**",
        "stop_loss_action": "Cắt toàn bộ",
        "target_text": ""
      }
    ],
    "position": {
      "status": "🟢 ĐANG GIỮ",
      "quantity": 100,
      "avg_cost": 192000,
      "entry_date": "2026-06-18",
      "invested_amount": 19200000
    },
    "buffett": "**Buffett check:** ...",
    "bull": [],
    "bear": []
  }
}
```

## Error shape

Future endpoints should use FastAPI's standard validation/error response. L3-03 does not add custom error handling.

## Authentication (L3-07)

The read endpoints and `/health` are public. All holdings write endpoints
require an `Authorization` header using the Bearer scheme:

```text
Authorization: Bearer <ADMIN_API_TOKEN>
```

The server reads `ADMIN_API_TOKEN` from its environment; the secret must not
be committed to the repository. Missing or invalid credentials return `401`
with `WWW-Authenticate: Bearer`. A valid request when the server has no
configured token returns `503` so writes fail closed.

## Write endpoints (L3-06, authenticated in L3-07)

Write operations are intentionally limited to portfolio holdings. They require
the L3-07 admin Bearer token described above.

### POST `/api/v1/stocks/holdings`

Creates a holding and returns HTTP `201`:

```json
{
  "ticker": "ACB",
  "quantity": 100,
  "avg_cost": 25000,
  "entry_date": "2026-08-04",
  "stop_loss": 23000,
  "status": "WATCHING",
  "note": "Created through the API",
  "targets": [27000, 30000]
}
```

The endpoint returns `{ "holding": ... }`. `ticker` is normalized to uppercase. A duplicate holding returns `409`.

### PATCH `/api/v1/stocks/holdings/{holding_id}`

Updates any supplied holding fields and replaces `targets` when that field is supplied. It returns the updated holding. Unknown IDs return `404`.

### DELETE `/api/v1/stocks/holdings/{holding_id}`

Deletes the holding and its target prices. It returns `204` on success and `404` for an unknown ID.

All write endpoints validate request bodies, require the admin bearer token,
and persist within the SQLite transaction opened by the API.

## Source mapping

The initial seed source is `apps/stocks-app/data/data.json`. L3-04 loads this fixture into SQLite and the FastAPI read endpoints map the relational rows back to this contract.
