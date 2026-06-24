-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Table 1: inventory_states (Hypertable for real-time inventory level tracking)
CREATE TABLE IF NOT EXISTS inventory_states (
    timestamp TIMESTAMPTZ NOT NULL,
    shop_id UUID NOT NULL,
    ingredient_id VARCHAR(50) NOT NULL,
    estimated_qty_grams NUMERIC(10, 2) NOT NULL,
    active_brewing_qty_grams NUMERIC(10, 2) NOT NULL,
    nearest_expiry TIMESTAMPTZ
);

-- Convert inventory_states into a hypertable partitioned by timestamp daily (86400000ms = 1 day)
SELECT create_hypertable('inventory_states', 'timestamp', if_not_exists => TRUE);

-- Table 2: brew_logs (FIFO logs for cooking/brewing events)
CREATE TABLE IF NOT EXISTS brew_logs (
    id UUID PRIMARY KEY,
    shop_id UUID NOT NULL,
    ingredient_id VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    initial_qty_grams NUMERIC(10, 2) NOT NULL,
    wasted_qty_grams NUMERIC(10, 2) DEFAULT 0.00
);

-- Create indexes for active brew queries
CREATE INDEX IF NOT EXISTS idx_brew_logs_active ON brew_logs (completed_at, expires_at) 
WHERE completed_at IS NOT NULL AND expires_at > NOW();

-- Table 3: recommendation_logs (Ops decisions and contexts)
CREATE TABLE IF NOT EXISTS recommendation_logs (
    id UUID PRIMARY KEY,
    shop_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ingredient_id VARCHAR(50) NOT NULL,
    action_recommended VARCHAR(50) NOT NULL, -- 'COOK_NOW', 'WAIT', 'WARN'
    predicted_shortage_at TIMESTAMPTZ,
    explanation_text TEXT NOT NULL,
    model_features_snapshot JSONB NOT NULL
);

-- Table 4: recommendation_feedback (Closed-loop staff response tracking)
CREATE TABLE IF NOT EXISTS recommendation_feedback (
    recommendation_id UUID PRIMARY KEY REFERENCES recommendation_logs(id) ON DELETE CASCADE,
    responded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    action_taken VARCHAR(50) NOT NULL, -- 'ACCEPTED', 'IGNORED', 'DELAYED'
    delay_minutes INT DEFAULT 0,
    staff_notes TEXT
);

-- Table 5: system_settings (key/value tuning parameters)
CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value VARCHAR(255) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table 6: sales_forecasts (forecasted demand history for feedback analytics)
CREATE TABLE IF NOT EXISTS sales_forecasts (
    id UUID PRIMARY KEY,
    shop_id UUID NOT NULL,
    ingredient_id VARCHAR(50) NOT NULL,
    forecast_time TIMESTAMPTZ NOT NULL,
    forecast_grams NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sales_forecasts_shop_time ON sales_forecasts (shop_id, forecast_time);

-- Table 7: sales_actuals (actual consumption / sales history for feedback analytics)
CREATE TABLE IF NOT EXISTS sales_actuals (
    id UUID PRIMARY KEY,
    shop_id UUID NOT NULL,
    ingredient_id VARCHAR(50) NOT NULL,
    actual_time TIMESTAMPTZ NOT NULL,
    actual_grams NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sales_actuals_shop_time ON sales_actuals (shop_id, actual_time);
