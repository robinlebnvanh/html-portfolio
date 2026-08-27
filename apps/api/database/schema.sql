PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS stocks (
    ticker TEXT PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolios (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    updated_at TEXT NOT NULL,
    note TEXT
);

CREATE TABLE IF NOT EXISTS holdings (
    id INTEGER PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id),
    ticker TEXT NOT NULL UNIQUE REFERENCES stocks(ticker),
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    avg_cost INTEGER NOT NULL CHECK (avg_cost >= 0),
    entry_date TEXT NOT NULL,
    stop_loss INTEGER CHECK (stop_loss IS NULL OR stop_loss >= 0),
    status TEXT NOT NULL,
    note TEXT
);

CREATE TABLE IF NOT EXISTS holding_targets (
    id INTEGER PRIMARY KEY,
    holding_id INTEGER NOT NULL REFERENCES holdings(id) ON DELETE CASCADE,
    target_order INTEGER NOT NULL CHECK (target_order > 0),
    price INTEGER NOT NULL CHECK (price >= 0),
    UNIQUE (holding_id, target_order)
);

CREATE TABLE IF NOT EXISTS watchlist_items (
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL REFERENCES stocks(ticker),
    PRIMARY KEY (portfolio_id, ticker)
);

CREATE TABLE IF NOT EXISTS journals (
    ticker TEXT PRIMARY KEY REFERENCES stocks(ticker),
    buffett TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS journal_snapshots (
    id INTEGER PRIMARY KEY,
    ticker TEXT NOT NULL REFERENCES journals(ticker) ON DELETE CASCADE,
    snapshot_date TEXT NOT NULL,
    price INTEGER NOT NULL CHECK (price >= 0),
    change_percent REAL,
    rsi REAL CHECK (rsi IS NULL OR (rsi >= 0 AND rsi <= 100)),
    macd TEXT,
    score TEXT,
    recommendation TEXT,
    note TEXT,
    UNIQUE (ticker, snapshot_date)
);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY,
    ticker TEXT NOT NULL REFERENCES journals(ticker) ON DELETE CASCADE,
    trade_date TEXT NOT NULL,
    trade_type TEXT NOT NULL,
    price INTEGER NOT NULL CHECK (price >= 0),
    stop_loss INTEGER CHECK (stop_loss IS NULL OR stop_loss >= 0),
    pnl TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS journal_entry_plans (
    id INTEGER PRIMARY KEY,
    ticker TEXT NOT NULL REFERENCES journals(ticker) ON DELETE CASCADE,
    plan_order INTEGER NOT NULL CHECK (plan_order > 0),
    condition TEXT NOT NULL,
    entry_text TEXT NOT NULL,
    stop_loss_action TEXT,
    target_text TEXT,
    UNIQUE (ticker, plan_order)
);

CREATE TABLE IF NOT EXISTS journal_positions (
    ticker TEXT PRIMARY KEY REFERENCES journals(ticker) ON DELETE CASCADE,
    status TEXT NOT NULL,
    quantity INTEGER CHECK (quantity IS NULL OR quantity >= 0),
    avg_cost INTEGER CHECK (avg_cost IS NULL OR avg_cost >= 0),
    entry_date TEXT,
    invested_amount INTEGER CHECK (invested_amount IS NULL OR invested_amount >= 0)
);

CREATE TABLE IF NOT EXISTS journal_theses (
    id INTEGER PRIMARY KEY,
    ticker TEXT NOT NULL REFERENCES journals(ticker) ON DELETE CASCADE,
    side TEXT NOT NULL CHECK (side IN ('bull', 'bear')),
    item_order INTEGER NOT NULL CHECK (item_order > 0),
    content TEXT NOT NULL,
    UNIQUE (ticker, side, item_order)
);

CREATE TABLE IF NOT EXISTS blog_posts (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL CHECK (status IN ('draft', 'published')),
    published_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin' CHECK (role IN ('admin')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS portfolio_content (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    hero_eyebrow TEXT NOT NULL,
    hero_title TEXT NOT NULL,
    hero_intro TEXT NOT NULL,
    hero_location TEXT NOT NULL,
    hero_experience TEXT NOT NULL,
    about_title TEXT NOT NULL,
    about_body TEXT NOT NULL,
    github_url TEXT NOT NULL,
    studio_title TEXT NOT NULL,
    studio_intro TEXT NOT NULL,
    offers TEXT NOT NULL,
    contact_title TEXT NOT NULL,
    contact_intro TEXT NOT NULL,
    contact_email TEXT NOT NULL,
    skills TEXT NOT NULL,
    projects TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS service_leads (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    business_name TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    email TEXT NOT NULL,
    preferred_date TEXT NOT NULL,
    package_name TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'proposal_sent', 'booked', 'closed')),
    admin_note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
