import os
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.blog_repository import (
    get_published_post,
    list_published_posts,
    seed_default_blog_posts,
)
from app.database import get_connection, initialize_database
from app.auth import require_admin_token
from app.stocks_repository import (
    create_holding,
    delete_holding,
    get_journals,
    get_portfolio,
    update_holding,
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


PostLimit = Annotated[int, Query(ge=1, le=20)]
PostOffset = Annotated[int, Query(ge=0)]


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
with get_connection() as startup_connection:
    seed_default_blog_posts(startup_connection)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Return the process health status."""
    return {"status": "ok", "service": "prj008-api"}


@app.get("/api/v1/stocks/portfolio", tags=["stocks"])
def portfolio() -> dict[str, Any]:
    """Return portfolio data read from SQLite."""
    with get_connection() as connection:
        return get_portfolio(connection)


@app.get("/api/v1/stocks/journals", tags=["stocks"])
def journals() -> dict[str, Any]:
    """Return ticker journals read from SQLite."""
    with get_connection() as connection:
        return get_journals(connection)


@app.get("/api/v1/blog/posts", tags=["blog"])
def blog_posts(limit: PostLimit = 6, offset: PostOffset = 0) -> dict[str, Any]:
    """Return published blog posts for the personal site."""
    with get_connection() as connection:
        return list_published_posts(connection, limit, offset)


@app.get("/api/v1/blog/posts/{slug}", tags=["blog"])
def blog_post(slug: str) -> dict[str, Any]:
    """Return one published blog post."""
    with get_connection() as connection:
        post = get_published_post(connection, slug)
    if post is None:
        raise HTTPException(status_code=404, detail="blog post not found")
    return {"post": post}


@app.post(
    "/api/v1/stocks/holdings",
    status_code=status.HTTP_201_CREATED,
    tags=["stocks"],
    dependencies=[Depends(require_admin_token)],
)
def create_portfolio_holding(payload: HoldingCreate) -> dict[str, Any]:
    """Create a holding and persist it to SQLite."""
    values = payload.model_dump()
    values["ticker"] = values["ticker"].strip().upper()
    if not values["ticker"]:
        raise HTTPException(status_code=422, detail="ticker must not be blank")

    with get_connection() as connection:
        if connection.execute(
            "SELECT 1 FROM holdings WHERE ticker = ?", (values["ticker"],)
        ).fetchone():
            raise HTTPException(status_code=409, detail="holding ticker already exists")
        return {"holding": create_holding(connection, values)}


@app.patch(
    "/api/v1/stocks/holdings/{holding_id}",
    tags=["stocks"],
    dependencies=[Depends(require_admin_token)],
)
def update_portfolio_holding(
    holding_id: int,
    payload: HoldingUpdate,
) -> dict[str, Any]:
    """Update selected holding fields and persist them to SQLite."""
    changes = payload.model_dump(exclude_unset=True)
    with get_connection() as connection:
        updated = update_holding(connection, holding_id, changes)
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
    """Delete a holding and its target prices from SQLite."""
    with get_connection() as connection:
        if not delete_holding(connection, holding_id):
            raise HTTPException(status_code=404, detail="holding not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
