# PRJ008 Admin Console Specification

## Stocks workspace

The Stocks workspace is a private, Bearer-authenticated operational console.
It reads data from the API and has five tabs: Holdings, Watchlist, Journals,
Trades, and Audit.

### Holdings and Trades

- **Trades** are the transaction ledger. `BUY`/`MUA` adds quantity and
  `SELL`/`BAN` reduces it.
- **Holdings** are derived current positions, rebuilt by the API from the
  ordered ledger for each ticker.
- Editing Holding quantity, average cost, entry date, or stop-loss creates an
  immutable `ADJUSTMENT` snapshot instead of overwriting a historical trade.
- Closing a Holding creates a zero-quantity adjustment. The UI confirmation
  must state that trade history is retained.
- API errors for oversell are displayed to the operator; the invalid change is
  not persisted.

Example: an operator corrects FPT from 100 to 90 shares. The console appends
an `ADJUSTMENT` record for 90 shares, while the original BUY transactions stay
in the ledger.

### Filters and summary

The shared Stocks filters support ticker, trade type, and date range. Ticker
filters apply across Holdings, Watchlist, Journals, Trades, and Audit; type and
date filters apply to Trades. The summary shows invested cost, open positions,
open quantity, stop-loss coverage, and total trade records.

Market-price and realized/unrealized P&L are intentionally not calculated in
this view because the API does not yet provide a trusted live market-price
source.

### Audit

The Audit tab reads `GET /api/v1/stocks/audit-logs`. It displays authenticated
Stocks mutations with actor, action, entity, ticker, timestamp, and a
before/after snapshot. The API is the source of audit records; the browser does
not create or modify audit entries.

## Blog workspace

The Blog workspace manages database-backed posts for the public personal site.
Each post supports draft/published status, tags, a cover image URL with alt text,
and inline article images inside `content` using Markdown image syntax.

Example inline image:

```md
![Admin overview loading state](https://example.com/admin-overview.png)
```

The Admin Console stores image URLs only. It does not upload binary image files;
image hosting remains external or static-site asset based.
