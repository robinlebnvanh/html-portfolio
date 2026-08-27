import os
from typing import Literal
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.blog_repository import (
    blog_slug_exists,
    create_blog_post,
    delete_blog_post,
    get_published_post,
    list_admin_posts,
    list_published_posts,
    seed_default_blog_posts,
    update_blog_post,
)
from app.auth import require_admin_token
from app.database import initialize_database
from app.sqlalchemy_database import get_session
from app.stocks_repository import (
    create_holding,
    create_trade,
    create_watchlist_item,
    delete_journal,
    delete_holding,
    delete_trade,
    delete_watchlist_item,
    get_journals,
    get_portfolio,
    holding_exists,
    journal_exists,
    upsert_journal,
    update_trade,
    update_holding,
    watchlist_exists,
)


TargetPrice = Annotated[int, Field(ge=0)]


class HoldingCreate(BaseModel):
    """Validated payload for creating a portfolio holding."""

    ticker: str = Field(min_length=1, max_length=12)
    quantity: int = Field(ge=0)
    avg_cost: int = Field(ge=0)
    entry_date: str = Field(min_length=1)
    stop_loss: int | None = Field(default=None, ge=0)
    status: str = Field(min_length=1, max_length=40)
    note: str | None = None
    targets: list[TargetPrice] = Field(default_factory=list)


class HoldingUpdate(BaseModel):
    """Partial validated payload for updating a portfolio holding."""

    quantity: int | None = Field(default=None, ge=0)
    avg_cost: int | None = Field(default=None, ge=0)
    entry_date: str | None = Field(default=None, min_length=1)
    stop_loss: int | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, min_length=1, max_length=40)
    note: str | None = None
    targets: list[TargetPrice] | None = None


class WatchlistCreate(BaseModel):
    """Validated payload for adding a watched ticker."""

    ticker: str = Field(min_length=1, max_length=12)


class JournalUpsert(BaseModel):
    """Validated payload for creating or updating a journal."""

    ticker: str = Field(min_length=1, max_length=12)
    buffett: str | None = ""
    bull: list[str] = Field(default_factory=list)
    bear: list[str] = Field(default_factory=list)


class JournalUpdate(BaseModel):
    """Partial validated payload for updating a journal."""

    buffett: str | None = None
    bull: list[str] | None = None
    bear: list[str] | None = None


class TradeCreate(BaseModel):
    """Validated payload for creating a journal trade."""

    ticker: str = Field(min_length=1, max_length=12)
    date: str = Field(min_length=1)
    type: str = Field(min_length=1, max_length=20)
    price: int = Field(ge=0)
    stop_loss: int | None = Field(default=None, ge=0)
    pnl: str | None = None
    note: str | None = None


class TradeUpdate(BaseModel):
    """Partial validated payload for updating a journal trade."""

    date: str | None = Field(default=None, min_length=1)
    type: str | None = Field(default=None, min_length=1, max_length=20)
    price: int | None = Field(default=None, ge=0)
    stop_loss: int | None = Field(default=None, ge=0)
    pnl: str | None = None
    note: str | None = None


class BlogPostCreate(BaseModel):
    """Validated payload for creating a database-backed blog post."""

    slug: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=180)
    summary: str = Field(min_length=1, max_length=600)
    content: str = Field(min_length=1)
    category: str = Field(min_length=1, max_length=80)
    tags: list[str] = Field(default_factory=list)
    status: Literal["draft", "published"] = "draft"
    published_at: str | None = None


class BlogPostUpdate(BaseModel):
    """Partial validated payload for updating a database-backed blog post."""

    slug: str | None = Field(default=None, min_length=1, max_length=120)
    title: str | None = Field(default=None, min_length=1, max_length=180)
    summary: str | None = Field(default=None, min_length=1, max_length=600)
    content: str | None = Field(default=None, min_length=1)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    tags: list[str] | None = None
    status: Literal["draft", "published"] | None = None
    published_at: str | None = None


PostLimit = Annotated[int, Query(ge=1, le=20)]
PostOffset = Annotated[int, Query(ge=0)]
AdminPostStatus = Annotated[Literal["all", "draft", "published"], Query()]


app = FastAPI(
    title="PRJ008 API",
    version="0.1.0",
    description="Backend API for the PRJ008 web development project.",
)

def configured_origins() -> list[str]:
    """Read explicit CORS origins for local or production deployment."""
    value = os.getenv(
        "API_ALLOWED_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000",
    )
    return [origin.strip() for origin in value.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)

initialize_database()
with get_session() as startup_session:
    seed_default_blog_posts(startup_session)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Return the process health status."""
    return {"status": "ok", "service": "prj008-api"}


@app.get("/api/v1/stocks/portfolio", tags=["stocks"])
def portfolio() -> dict[str, Any]:
    """Return portfolio data read through SQLAlchemy."""
    with get_session() as session:
        return get_portfolio(session)


@app.get("/api/v1/stocks/journals", tags=["stocks"])
def journals() -> dict[str, Any]:
    """Return ticker journals read through SQLAlchemy."""
    with get_session() as session:
        return get_journals(session)


@app.get("/api/v1/blog/posts", tags=["blog"])
def blog_posts(limit: PostLimit = 6, offset: PostOffset = 0) -> dict[str, Any]:
    """Return published blog posts for the personal site."""
    with get_session() as session:
        return list_published_posts(session, limit, offset)


@app.get("/api/v1/blog/posts/{slug}", tags=["blog"])
def blog_post(slug: str) -> dict[str, Any]:
    """Return one published blog post."""
    with get_session() as session:
        post = get_published_post(session, slug)
    if post is None:
        raise HTTPException(status_code=404, detail="blog post not found")
    return {"post": post}


def normalize_blog_slug(slug: str) -> str:
    """Normalize a slug while keeping validation explicit."""
    normalized = slug.strip().lower()
    if not normalized:
        raise HTTPException(status_code=422, detail="slug must not be blank")
    return normalized


def clean_blog_payload(values: dict[str, Any]) -> dict[str, Any]:
    """Trim text fields from blog write payloads."""
    cleaned = dict(values)
    if "slug" in cleaned and cleaned["slug"] is not None:
        cleaned["slug"] = normalize_blog_slug(cleaned["slug"])
    for key in ("title", "summary", "content", "category", "published_at"):
        if key in cleaned and isinstance(cleaned[key], str):
            cleaned[key] = cleaned[key].strip()
            if key != "published_at" and not cleaned[key]:
                raise HTTPException(status_code=422, detail=f"{key} must not be blank")
    if "tags" in cleaned and cleaned["tags"] is not None:
        cleaned["tags"] = [tag.strip() for tag in cleaned["tags"] if tag.strip()]
    return cleaned


@app.get(
    "/api/v1/admin/blog/posts",
    tags=["blog-admin"],
    dependencies=[Depends(require_admin_token)],
)
def admin_blog_posts(status_filter: AdminPostStatus = "all") -> dict[str, Any]:
    """Return draft and published blog posts for the admin UI."""
    with get_session() as session:
        return list_admin_posts(
            session,
            status_filter=None if status_filter == "all" else status_filter,
        )


@app.post(
    "/api/v1/admin/blog/posts",
    status_code=status.HTTP_201_CREATED,
    tags=["blog-admin"],
    dependencies=[Depends(require_admin_token)],
)
def create_admin_blog_post(payload: BlogPostCreate) -> dict[str, Any]:
    """Create a blog post through the authenticated admin API."""
    values = clean_blog_payload(payload.model_dump())
    with get_session() as session:
        if blog_slug_exists(session, values["slug"]):
            raise HTTPException(status_code=409, detail="blog slug already exists")
        return {"post": create_blog_post(session, values)}


@app.patch(
    "/api/v1/admin/blog/posts/{post_id}",
    tags=["blog-admin"],
    dependencies=[Depends(require_admin_token)],
)
def update_admin_blog_post(post_id: int, payload: BlogPostUpdate) -> dict[str, Any]:
    """Update one blog post through the authenticated admin API."""
    changes = clean_blog_payload(payload.model_dump(exclude_unset=True))
    with get_session() as session:
        if "slug" in changes and blog_slug_exists(session, changes["slug"], post_id):
            raise HTTPException(status_code=409, detail="blog slug already exists")
        updated = update_blog_post(session, post_id, changes)
        if updated is None:
            raise HTTPException(status_code=404, detail="blog post not found")
        return {"post": updated}


@app.delete(
    "/api/v1/admin/blog/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["blog-admin"],
    dependencies=[Depends(require_admin_token)],
)
def delete_admin_blog_post(post_id: int) -> Response:
    """Delete one blog post through the authenticated admin API."""
    with get_session() as session:
        if not delete_blog_post(session, post_id):
            raise HTTPException(status_code=404, detail="blog post not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/api/v1/stocks/holdings",
    status_code=status.HTTP_201_CREATED,
    tags=["stocks"],
    dependencies=[Depends(require_admin_token)],
)
def create_portfolio_holding(payload: HoldingCreate) -> dict[str, Any]:
    """Create a holding and persist it through SQLAlchemy."""
    values = payload.model_dump()
    values["ticker"] = values["ticker"].strip().upper()
    if not values["ticker"]:
        raise HTTPException(status_code=422, detail="ticker must not be blank")

    with get_session() as session:
        if holding_exists(session, values["ticker"]):
            raise HTTPException(status_code=409, detail="holding ticker already exists")
        return {"holding": create_holding(session, values)}


@app.patch(
    "/api/v1/stocks/holdings/{holding_id}",
    tags=["stocks"],
    dependencies=[Depends(require_admin_token)],
)
def update_portfolio_holding(
    holding_id: int,
    payload: HoldingUpdate,
) -> dict[str, Any]:
    """Update selected holding fields and persist them through SQLAlchemy."""
    changes = payload.model_dump(exclude_unset=True)
    with get_session() as session:
        updated = update_holding(session, holding_id, changes)
        if updated is None:
            raise HTTPException(status_code=404, detail="holding not found")
        return {"holding": updated}


@app.delete(
    "/api/v1/stocks/holdings/{holding_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["stocks"],
    dependencies=[Depends(require_admin_token)],
)
def delete_portfolio_holding(holding_id: int) -> Response:
    """Delete a holding and its target prices through SQLAlchemy."""
    with get_session() as session:
        if not delete_holding(session, holding_id):
            raise HTTPException(status_code=404, detail="holding not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/api/v1/stocks/watchlist",
    status_code=status.HTTP_201_CREATED,
    tags=["stocks"],
    dependencies=[Depends(require_admin_token)],
)
def create_portfolio_watchlist_item(payload: WatchlistCreate) -> dict[str, Any]:
    """Add a ticker to the portfolio watchlist."""
    ticker = payload.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=422, detail="ticker must not be blank")

    with get_session() as session:
        if watchlist_exists(session, ticker):
            raise HTTPException(status_code=409, detail="watchlist ticker already exists")
        return {"watchlist_item": create_watchlist_item(session, ticker)}


@app.delete(
    "/api/v1/stocks/watchlist/{ticker}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["stocks"],
    dependencies=[Depends(require_admin_token)],
)
def delete_portfolio_watchlist_item(ticker: str) -> Response:
    """Remove a ticker from the portfolio watchlist."""
    with get_session() as session:
        if not delete_watchlist_item(session, ticker.strip().upper()):
            raise HTTPException(status_code=404, detail="watchlist ticker not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/api/v1/stocks/journals",
    status_code=status.HTTP_201_CREATED,
    tags=["stocks"],
    dependencies=[Depends(require_admin_token)],
)
def create_stock_journal(payload: JournalUpsert) -> dict[str, Any]:
    """Create a journal with thesis fields."""
    values = payload.model_dump()
    ticker = values.pop("ticker").strip().upper()
    if not ticker:
        raise HTTPException(status_code=422, detail="ticker must not be blank")

    with get_session() as session:
        if journal_exists(session, ticker):
            raise HTTPException(status_code=409, detail="journal ticker already exists")
        return {"journal": upsert_journal(session, ticker, values)}


@app.patch(
    "/api/v1/stocks/journals/{ticker}",
    tags=["stocks"],
    dependencies=[Depends(require_admin_token)],
)
def update_stock_journal(ticker: str, payload: JournalUpdate) -> dict[str, Any]:
    """Update a journal's editable thesis fields."""
    normalized_ticker = ticker.strip().upper()
    changes = payload.model_dump(exclude_unset=True)

    with get_session() as session:
        if not journal_exists(session, normalized_ticker):
            raise HTTPException(status_code=404, detail="journal not found")
        return {"journal": upsert_journal(session, normalized_ticker, changes)}


@app.delete(
    "/api/v1/stocks/journals/{ticker}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["stocks"],
    dependencies=[Depends(require_admin_token)],
)
def delete_stock_journal(ticker: str) -> Response:
    """Delete a journal and its child rows."""
    with get_session() as session:
        if not delete_journal(session, ticker.strip().upper()):
            raise HTTPException(status_code=404, detail="journal not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/api/v1/stocks/trades",
    status_code=status.HTTP_201_CREATED,
    tags=["stocks"],
    dependencies=[Depends(require_admin_token)],
)
def create_stock_trade(payload: TradeCreate) -> dict[str, Any]:
    """Create a trade row for a ticker journal."""
    values = payload.model_dump()
    values["ticker"] = values["ticker"].strip().upper()
    values["type"] = values["type"].strip().upper()
    if not values["ticker"]:
        raise HTTPException(status_code=422, detail="ticker must not be blank")
    if not values["type"]:
        raise HTTPException(status_code=422, detail="type must not be blank")

    with get_session() as session:
        return {"trade": create_trade(session, values)}


@app.patch(
    "/api/v1/stocks/trades/{trade_id}",
    tags=["stocks"],
    dependencies=[Depends(require_admin_token)],
)
def update_stock_trade(trade_id: int, payload: TradeUpdate) -> dict[str, Any]:
    """Update selected fields on a trade row."""
    changes = payload.model_dump(exclude_unset=True)
    if "type" in changes and changes["type"] is not None:
        changes["type"] = changes["type"].strip().upper()
        if not changes["type"]:
            raise HTTPException(status_code=422, detail="type must not be blank")

    with get_session() as session:
        updated = update_trade(session, trade_id, changes)
        if updated is None:
            raise HTTPException(status_code=404, detail="trade not found")
        return {"trade": updated}


@app.delete(
    "/api/v1/stocks/trades/{trade_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["stocks"],
    dependencies=[Depends(require_admin_token)],
)
def delete_stock_trade(trade_id: int) -> Response:
    """Delete one trade row."""
    with get_session() as session:
        if not delete_trade(session, trade_id):
            raise HTTPException(status_code=404, detail="trade not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
