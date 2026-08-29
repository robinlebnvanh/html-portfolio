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

Admin-only. Requires an `Authorization: Bearer <token>` header.

Returns the current private portfolio summary, holdings, and watchlist.
Holdings include their stable numeric `id`, which the Admin UI uses for
PATCH/DELETE.

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

Admin-only. Requires an `Authorization: Bearer <token>` header.

Returns private journal data keyed by ticker.

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

## Blog endpoints

Blog posts are backend-owned data stored in SQLite table `blog_posts`.
The personal site reads them through FastAPI instead of static JSON.

### GET `/api/v1/blog/posts`

Returns published posts with pagination:

```json
{
  "posts": [
    {
      "id": 1,
      "slug": "backend-blog-api",
      "title": "Building a backend-powered blog",
      "summary": "Why this portfolio stores blog posts in SQLite and serves them through FastAPI.",
      "category": "backend",
      "tags": ["FastAPI", "SQLite", "Portfolio"],
      "published_at": "2026-08-05",
      "updated_at": "2026-08-05 10:00:00"
    }
  ],
  "total": 2,
  "limit": 4,
  "offset": 0,
  "has_more": false
}
```

### GET `/api/v1/blog/posts/{slug}`

Returns one published post with full `content`. Unknown slugs return `404`.

### Admin blog endpoints

Blog management uses the same admin Bearer token as the stocks Admin UI. These
endpoints read and write the `blog_posts` database table.

#### GET `/api/v1/admin/blog/posts`

Returns draft and published posts for the admin UI. Optional
`status_filter=all|draft|published` narrows the result. The response includes
full `content` and `status`:

```json
{
  "posts": [
    {
      "id": 1,
      "slug": "backend-blog-api",
      "title": "Building a backend-powered blog",
      "summary": "Why this portfolio stores blog posts in SQLite and serves them through FastAPI.",
      "content": "Full article content",
      "category": "backend",
      "tags": ["FastAPI", "SQLite", "Portfolio"],
      "status": "published",
      "published_at": "2026-08-05",
      "updated_at": "2026-08-27 10:00:00"
    }
  ],
  "total": 1
}
```

#### POST `/api/v1/admin/blog/posts`

Creates a post and returns HTTP `201`.

```json
{
  "slug": "database-backed-blog",
  "title": "Building a database-backed blog",
  "summary": "How the portfolio blog is managed through FastAPI and PostgreSQL.",
  "content": "Full post content",
  "category": "backend",
  "tags": ["FastAPI", "PostgreSQL"],
  "status": "draft",
  "published_at": null
}
```

Duplicate slugs return `409`. Publishing without `published_at` sets today's
date.

#### PATCH `/api/v1/admin/blog/posts/{post_id}`

Updates any supplied post fields and returns the updated post. Unknown IDs
return `404`; duplicate slugs return `409`.

#### DELETE `/api/v1/admin/blog/posts/{post_id}`

Deletes one post. It returns `204` on success and `404` for an unknown ID.

## Authentication (L3-07)

The read endpoints and `/health` are public. All admin/write endpoints
require an `Authorization` header using the Bearer scheme:

```text
Authorization: Bearer <ADMIN_API_TOKEN>
```

The server reads `ADMIN_API_TOKEN` from its environment; the secret must not
be committed to the repository. Missing or invalid credentials return `401`
with `WWW-Authenticate: Bearer`. A valid request when the server has no
configured token returns `503` so writes fail closed.

## Write endpoints (L3-06, authenticated in L3-07)

Write operations cover holdings, watchlist items, journal thesis fields, and
trade rows. They require the L3-07 admin Bearer token described above.

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
and persist within the database transaction opened by the API.

### POST `/api/v1/stocks/watchlist`

Adds one ticker to the portfolio watchlist:

```json
{"ticker": "ACB"}
```

The endpoint returns `{ "watchlist_item": { "ticker": "ACB" } }`. Duplicate
tickers return `409`.

### DELETE `/api/v1/stocks/watchlist/{ticker}`

Removes one ticker from the portfolio watchlist. Unknown tickers return `404`.

### POST `/api/v1/stocks/journals`

Creates a ticker journal and optional thesis lists:

```json
{
  "ticker": "ACB",
  "buffett": "Buffett check text",
  "bull": ["Strong deposit growth"],
  "bear": ["Valuation risk"]
}
```

The endpoint returns `{ "journal": ... }` using the same journal shape as
`GET /api/v1/stocks/journals`. Duplicate journals return `409`.

### PATCH `/api/v1/stocks/journals/{ticker}`

Updates `buffett`, `bull`, and/or `bear`. Supplying `bull` or `bear` replaces
that full list. Unknown journals return `404`.

### DELETE `/api/v1/stocks/journals/{ticker}`

Deletes the journal and its child rows: snapshots, trades, entry plans,
position, and theses. Unknown journals return `404`.

### POST `/api/v1/stocks/trades`

Creates a trade row and creates an empty journal for the ticker if needed:

```json
{
  "ticker": "ACB",
  "date": "2026-08-27",
  "type": "BUY",
  "price": 25000,
  "stop_loss": 23000,
  "pnl": "0",
  "note": "Initial entry"
}
```

The endpoint returns `{ "trade": ... }`. Trade rows returned by
`GET /api/v1/stocks/journals` include stable numeric `id` and `ticker` fields
for Admin UI edit/delete actions.

### PATCH `/api/v1/stocks/trades/{trade_id}`

Updates any supplied trade fields except ticker. Unknown trades return `404`.

### DELETE `/api/v1/stocks/trades/{trade_id}`

Deletes one trade row. Unknown trades return `404`.

## Service lead endpoints (P2-11)

Service-business demo sites can submit booking or proposal inquiries through
the public lead endpoint. Admin review stays behind the same Bearer-protected
Admin Console boundary as the other write workflows.

### POST `/api/v1/leads`

Creates one service-business inquiry and returns HTTP `201`:

```json
{
  "source": "wedding-planner-demo",
  "business_name": "Maison Vow",
  "customer_name": "Smoke Client",
  "email": "smoke@example.com",
  "preferred_date": "2026-10-10",
  "package_name": "Partial Planning",
  "message": "Need vendor coordination and planning timeline."
}
```

The endpoint returns `{ "lead": ... }`. New leads start with status `new`.
Blank trimmed fields return `422`.

### GET `/api/v1/admin/leads`

Returns service leads for the Admin Console. It requires the admin Bearer token
and accepts `status_filter=all|new|contacted|proposal_sent|booked|closed` plus
optional `q` search across customer, business, contact, package, and message.

```json
{
  "total": 1,
  "leads": [
    {
      "id": 1,
  "source": "wedding-planner-demo",
  "channel": "form",
  "business_name": "Maison Vow",
  "customer_name": "Smoke Client",
  "email": "smoke@example.com",
  "phone": null,
  "preferred_date": "2026-10-10",
  "follow_up_at": null,
  "package_name": "Partial Planning",
  "message": "Need vendor coordination and planning timeline.",
  "status": "new",
  "job_stage": null,
  "quoted_amount": null,
  "quote_currency": null,
  "deadline_at": null,
  "file_url": null,
  "delivery_url": null,
  "revision_count": 0,
  "paid_at": null,
      "admin_note": null,
      "created_at": "2026-08-28T00:00:00",
      "updated_at": "2026-08-28T00:00:00"
    }
  ]
}
```

Missing or invalid admin credentials return `401`.

### POST `/api/v1/admin/leads`

Creates one manual lead from a direct channel such as phone, email, Zalo,
Facebook, Instagram, or referral. It requires the admin Bearer token.

```json
{
  "source": "admin-manual",
  "channel": "phone",
  "business_name": "Robin Le Portfolio",
  "customer_name": "Phone Client",
  "email": null,
  "phone": "+84900000000",
  "preferred_date": null,
  "follow_up_at": "2026-09-02",
  "package_name": "Portfolio contact",
  "message": "Called to ask about a booking workflow."
}
```

Manual leads require at least one contact method: `email` or `phone`.

### PATCH `/api/v1/admin/leads/{lead_id}`

Updates admin-owned workflow fields:

```json
{
  "status": "proposal_sent",
  "admin_note": "Send planning proposal.",
  "follow_up_at": "2026-09-02",
  "job_stage": "editing",
  "quoted_amount": 180,
  "quote_currency": "AUD",
  "deadline_at": "2026-09-04",
  "file_url": "https://drive.example/client-files",
  "delivery_url": "https://drive.example/final-files",
  "revision_count": 1,
  "paid_at": null
}
```

Allowed statuses are `new`, `contacted`, `proposal_sent`, `booked`, and
`closed`. Allowed job stages are `awaiting_files`, `editing`, `review`,
`revision`, `delivered`, and `paid`. Unknown IDs return `404`.

The Admin Console uses these fields to turn a booked Photoshop inquiry into a
trackable job: client files, quote, currency, deadline, revision count, delivery
link, and paid date.

### POST `/api/v1/admin/leads/{lead_id}/activities`

Adds one timeline activity to a lead. It requires the admin Bearer token.

```json
{
  "activity_type": "phone_call",
  "note": "Client asked for pricing and availability."
}
```

## Source mapping

The initial seed source is `apps/stocks-app/data/data.json`. L3-04 loads this fixture into SQLite and the FastAPI read endpoints map the relational rows back to this contract.
