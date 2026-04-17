"""SQLite database schema definitions for historical metrics storage."""

# Main daily metrics table - stores aggregated daily business metrics
DAILY_METRICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_metrics (
    date TEXT PRIMARY KEY,

    -- Revenue metrics
    revenue_total REAL DEFAULT 0.0,
    revenue_medical REAL DEFAULT 0.0,
    revenue_beauty REAL DEFAULT 0.0,
    revenue_paid REAL DEFAULT 0.0,
    revenue_pending REAL DEFAULT 0.0,

    -- Order metrics
    orders_total INTEGER DEFAULT 0,
    orders_completed INTEGER DEFAULT 0,
    orders_pending INTEGER DEFAULT 0,
    orders_cancelled INTEGER DEFAULT 0,
    avg_order_value REAL DEFAULT 0.0,
    completion_rate REAL DEFAULT 0.0,

    -- User metrics
    users_total INTEGER DEFAULT 0,
    doctors_total INTEGER DEFAULT 0,
    new_signups INTEGER DEFAULT 0,
    approved_users INTEGER DEFAULT 0,
    approval_rate REAL DEFAULT 0.0,

    -- Advertisement metrics
    ads_total INTEGER DEFAULT 0,
    ads_active INTEGER DEFAULT 0,
    ads_pending INTEGER DEFAULT 0,
    ads_revenue REAL DEFAULT 0.0,

    -- Collection metrics
    collection_rate REAL DEFAULT 0.0,
    pending_amount REAL DEFAULT 0.0,

    -- Research metrics
    research_papers INTEGER DEFAULT 0,
    research_views INTEGER DEFAULT 0,
    research_upvotes INTEGER DEFAULT 0,

    -- Financial tracking KPIs (from manual sheet)
    fin_sales_target REAL DEFAULT 0.0,
    fin_sales_actual REAL DEFAULT 0.0,
    fin_sales_achievement REAL DEFAULT 0.0,
    fin_investment_total REAL DEFAULT 0.0,
    fin_expenses_total REAL DEFAULT 0.0,
    fin_profit REAL DEFAULT 0.0,
    fin_roi REAL DEFAULT 0.0,
    fin_profit_margin REAL DEFAULT 0.0,
    fin_debt_ratio REAL DEFAULT 0.0,
    fin_cac REAL DEFAULT 0.0,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Index for faster date range queries
DAILY_METRICS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date);
CREATE INDEX IF NOT EXISTS idx_daily_metrics_revenue ON daily_metrics(revenue_total);
CREATE INDEX IF NOT EXISTS idx_daily_metrics_orders ON daily_metrics(orders_total);
"""

# Financial KPIs table - stores detailed financial tracking data
FINANCIAL_KPIS_SCHEMA = """
CREATE TABLE IF NOT EXISTS financial_kpis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    year INTEGER NOT NULL,
    month TEXT NOT NULL,
    record_type TEXT DEFAULT 'daily',

    -- Sales breakdown
    medical_sales_target REAL DEFAULT 0.0,
    medical_sales_actual REAL DEFAULT 0.0,
    beauty_sales_target REAL DEFAULT 0.0,
    beauty_sales_actual REAL DEFAULT 0.0,

    -- Investment breakdown
    founder_investment REAL DEFAULT 0.0,
    cofounder_investment REAL DEFAULT 0.0,
    investor_investment REAL DEFAULT 0.0,
    importer_investment REAL DEFAULT 0.0,

    -- Calculated KPIs
    roi_percent REAL DEFAULT 0.0,
    profit_margin_percent REAL DEFAULT 0.0,
    cac REAL DEFAULT 0.0,
    debt_ratio_percent REAL DEFAULT 0.0,
    collection_efficiency REAL DEFAULT 0.0,
    sales_growth_percent REAL DEFAULT 0.0,
    client_growth_percent REAL DEFAULT 0.0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(date, record_type)
);
"""

# Alerts history table - stores detected anomalies and alerts
ALERTS_HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS alerts_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT DEFAULT 'warning',
    metric_name TEXT NOT NULL,
    current_value REAL,
    threshold_value REAL,
    deviation REAL,
    message TEXT,
    acknowledged INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Forecasts table - stores generated predictions
FORECASTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    forecast_date TEXT NOT NULL,
    target_date TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    predicted_value REAL,
    confidence_lower REAL,
    confidence_upper REAL,
    confidence_level REAL DEFAULT 0.85,
    model_used TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(forecast_date, target_date, metric_name)
);
"""

# All schemas combined for initialization
ALL_SCHEMAS = [
    DAILY_METRICS_SCHEMA,
    DAILY_METRICS_INDEXES,
    FINANCIAL_KPIS_SCHEMA,
    ALERTS_HISTORY_SCHEMA,
    FORECASTS_SCHEMA,
]

# Column mapping for daily metrics extraction from analyzers
METRICS_COLUMN_MAPPING = {
    # Revenue
    "revenue_total": ["total_revenue", "total_paid_amount"],
    "revenue_paid": ["total_paid_amount"],
    "revenue_pending": ["total_pending_amount"],
    # Orders
    "orders_total": ["total_orders"],
    "orders_completed": ["completed_orders"],
    "orders_pending": ["pending_orders"],
    "avg_order_value": ["avg_order_value"],
    "completion_rate": ["payment_completion_rate"],
    # Users
    "users_total": ["total_users"],
    "doctors_total": ["total_doctors"],
    "approved_users": ["approved_users"],
    # Ads
    "ads_total": ["total_ads"],
    "ads_pending": ["pending_ads"],
    # Research
    "research_papers": ["total_papers"],
    "research_views": ["total_views"],
    "research_upvotes": ["total_upvotes"],
}

