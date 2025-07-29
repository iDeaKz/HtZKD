-- 🚀 LivePrecisionCalculator - Database Schema
-- =============================================
-- 
-- Production-ready SQLite schema for quantum-precision calculations
-- with comprehensive error tracking and system metrics.

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Calculations table - stores all precision calculations
CREATE TABLE IF NOT EXISTS calculations (
    id TEXT PRIMARY KEY,
    operand1 TEXT NOT NULL,
    operand2 TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('add', 'subtract', 'multiply', 'divide', 'power')),
    result TEXT NOT NULL,
    precision_used INTEGER NOT NULL CHECK (precision_used > 0 AND precision_used <= 60),
    currency TEXT DEFAULT 'USD' CHECK (length(currency) = 3),
    timestamp TEXT NOT NULL,
    calculation_time_ms REAL,
    client_id TEXT,
    client_ip TEXT,
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_calculations_timestamp (timestamp),
    INDEX idx_calculations_currency (currency),
    INDEX idx_calculations_operation (operation),
    INDEX idx_calculations_created_at (created_at)
);

-- Exchange rates table - tracks currency exchange rates
CREATE TABLE IF NOT EXISTS exchange_rates (
    currency TEXT PRIMARY KEY CHECK (length(currency) = 3),
    rate TEXT NOT NULL,
    rate_decimal REAL NOT NULL,
    source TEXT DEFAULT 'internal',
    last_updated TEXT NOT NULL,
    volatility REAL DEFAULT 0.0,
    trend TEXT CHECK (trend IN ('up', 'down', 'stable')) DEFAULT 'stable',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_exchange_rates_updated_at (updated_at),
    INDEX idx_exchange_rates_volatility (volatility)
);

-- Error healing events table - comprehensive error tracking
CREATE TABLE IF NOT EXISTS healing_events (
    id TEXT PRIMARY KEY,
    error_type TEXT NOT NULL,
    error_code TEXT,
    error_message TEXT,
    error_context TEXT, -- JSON string with additional context
    healing_action TEXT NOT NULL,
    healing_strategy TEXT,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    healing_time_ms REAL,
    resilience_score_before REAL,
    resilience_score_after REAL,
    auto_corrected BOOLEAN DEFAULT FALSE,
    correction_applied TEXT,
    timestamp TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_healing_events_error_type (error_type),
    INDEX idx_healing_events_success (success),
    INDEX idx_healing_events_timestamp (timestamp),
    INDEX idx_healing_events_created_at (created_at)
);

-- System metrics table - performance and health monitoring
CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_type TEXT NOT NULL CHECK (metric_type IN ('performance', 'health', 'usage', 'error')),
    active_connections INTEGER DEFAULT 0,
    calculations_per_minute INTEGER DEFAULT 0,
    cache_hit_ratio REAL DEFAULT 0.0 CHECK (cache_hit_ratio >= 0.0 AND cache_hit_ratio <= 1.0),
    memory_usage_mb REAL DEFAULT 0.0,
    cpu_usage_percent REAL DEFAULT 0.0,
    disk_usage_percent REAL DEFAULT 0.0,
    uptime_seconds INTEGER DEFAULT 0,
    error_rate REAL DEFAULT 0.0 CHECK (error_rate >= 0.0 AND error_rate <= 1.0),
    response_time_ms REAL DEFAULT 0.0,
    throughput_requests_per_sec REAL DEFAULT 0.0,
    websocket_connections INTEGER DEFAULT 0,
    redis_status TEXT CHECK (redis_status IN ('connected', 'disconnected', 'error')) DEFAULT 'disconnected',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_system_metrics_type (metric_type),
    INDEX idx_system_metrics_timestamp (timestamp)
);

-- WebSocket connections table - track active connections
CREATE TABLE IF NOT EXISTS websocket_connections (
    connection_id TEXT PRIMARY KEY,
    client_ip TEXT,
    user_agent TEXT,
    connected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_ping DATETIME,
    last_pong DATETIME,
    messages_sent INTEGER DEFAULT 0,
    messages_received INTEGER DEFAULT 0,
    status TEXT CHECK (status IN ('connected', 'disconnected', 'error')) DEFAULT 'connected',
    disconnect_reason TEXT,
    disconnected_at DATETIME,
    
    INDEX idx_websocket_connections_status (status),
    INDEX idx_websocket_connections_connected_at (connected_at)
);

-- Calculation batches table - for batch processing tracking
CREATE TABLE IF NOT EXISTS calculation_batches (
    batch_id TEXT PRIMARY KEY,
    total_calculations INTEGER NOT NULL CHECK (total_calculations > 0),
    completed_calculations INTEGER DEFAULT 0,
    failed_calculations INTEGER DEFAULT 0,
    batch_status TEXT CHECK (batch_status IN ('pending', 'processing', 'completed', 'failed')) DEFAULT 'pending',
    started_at DATETIME,
    completed_at DATETIME,
    processing_time_ms REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_calculation_batches_status (batch_status),
    INDEX idx_calculation_batches_created_at (created_at)
);

-- API usage tracking table - for monitoring and rate limiting
CREATE TABLE IF NOT EXISTS api_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL CHECK (method IN ('GET', 'POST', 'PUT', 'DELETE', 'WebSocket')),
    client_ip TEXT,
    user_agent TEXT,
    response_status INTEGER,
    response_time_ms REAL,
    request_size_bytes INTEGER DEFAULT 0,
    response_size_bytes INTEGER DEFAULT 0,
    error_message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_api_usage_endpoint (endpoint),
    INDEX idx_api_usage_client_ip (client_ip),
    INDEX idx_api_usage_timestamp (timestamp),
    INDEX idx_api_usage_status (response_status)
);

-- Configuration table - store application configuration
CREATE TABLE IF NOT EXISTS configuration (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'general',
    is_sensitive BOOLEAN DEFAULT FALSE,
    updated_by TEXT DEFAULT 'system',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_configuration_category (category)
);

-- Performance benchmarks table - track calculation performance
CREATE TABLE IF NOT EXISTS performance_benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type TEXT NOT NULL,
    precision_level INTEGER NOT NULL,
    operand_complexity TEXT CHECK (operand_complexity IN ('simple', 'moderate', 'complex', 'extreme')),
    execution_time_ms REAL NOT NULL,
    memory_usage_mb REAL,
    cache_hit BOOLEAN DEFAULT FALSE,
    optimization_applied TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_performance_benchmarks_operation (operation_type),
    INDEX idx_performance_benchmarks_precision (precision_level),
    INDEX idx_performance_benchmarks_timestamp (timestamp)
);

-- Error patterns table - machine learning for error prediction
CREATE TABLE IF NOT EXISTS error_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_hash TEXT UNIQUE NOT NULL,
    error_signature TEXT NOT NULL,
    frequency INTEGER DEFAULT 1,
    last_occurrence DATETIME DEFAULT CURRENT_TIMESTAMP,
    prediction_confidence REAL DEFAULT 0.0 CHECK (prediction_confidence >= 0.0 AND prediction_confidence <= 1.0),
    mitigation_strategy TEXT,
    success_rate REAL DEFAULT 0.0 CHECK (success_rate >= 0.0 AND success_rate <= 1.0),
    
    INDEX idx_error_patterns_frequency (frequency),
    INDEX idx_error_patterns_confidence (prediction_confidence),
    INDEX idx_error_patterns_last_occurrence (last_occurrence)
);

-- Audit log table - comprehensive security and change tracking
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    action TEXT NOT NULL,
    old_values TEXT, -- JSON string
    new_values TEXT, -- JSON string
    user_id TEXT,
    client_ip TEXT,
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_audit_log_event_type (event_type),
    INDEX idx_audit_log_resource_type (resource_type),
    INDEX idx_audit_log_timestamp (timestamp),
    INDEX idx_audit_log_user_id (user_id)
);

-- Insert default configuration
INSERT OR IGNORE INTO configuration (key, value, description, category) VALUES 
    ('precision_default', '50', 'Default calculation precision in decimal places', 'calculation'),
    ('max_precision', '60', 'Maximum allowed calculation precision', 'calculation'),
    ('cache_ttl_seconds', '3600', 'Default cache time-to-live in seconds', 'cache'),
    ('max_websocket_connections', '1000', 'Maximum concurrent WebSocket connections', 'websocket'),
    ('exchange_rate_update_interval', '60', 'Exchange rate update interval in seconds', 'currency'),
    ('error_resilience_threshold', '0.95', 'Minimum resilience score threshold', 'healing'),
    ('batch_size_limit', '1000', 'Maximum calculations per batch', 'batch'),
    ('api_rate_limit_per_minute', '1000', 'API requests per minute limit', 'api'),
    ('performance_monitoring_enabled', 'true', 'Enable performance monitoring', 'monitoring'),
    ('auto_healing_enabled', 'true', 'Enable automatic error healing', 'healing');

-- Insert supported currencies
INSERT OR IGNORE INTO exchange_rates (currency, rate, rate_decimal, source, last_updated) VALUES 
    ('USD', '1.0', 1.0, 'base', datetime('now')),
    ('EUR', '0.85', 0.85, 'internal', datetime('now')),
    ('GBP', '0.73', 0.73, 'internal', datetime('now')),
    ('JPY', '110.0', 110.0, 'internal', datetime('now')),
    ('AUD', '1.35', 1.35, 'internal', datetime('now')),
    ('CAD', '1.25', 1.25, 'internal', datetime('now')),
    ('CHF', '0.92', 0.92, 'internal', datetime('now')),
    ('CNY', '6.45', 6.45, 'internal', datetime('now')),
    ('SEK', '8.60', 8.60, 'internal', datetime('now')),
    ('NZD', '1.42', 1.42, 'internal', datetime('now'));

-- Create views for common queries
CREATE VIEW IF NOT EXISTS calculation_summary AS
SELECT 
    operation,
    currency,
    COUNT(*) as total_calculations,
    AVG(precision_used) as avg_precision,
    AVG(calculation_time_ms) as avg_time_ms,
    DATE(created_at) as calculation_date
FROM calculations 
GROUP BY operation, currency, DATE(created_at);

CREATE VIEW IF NOT EXISTS error_healing_summary AS
SELECT 
    error_type,
    COUNT(*) as total_events,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_healings,
    ROUND(AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) * 100, 2) as success_rate_percent,
    AVG(healing_time_ms) as avg_healing_time_ms,
    DATE(created_at) as event_date
FROM healing_events 
GROUP BY error_type, DATE(created_at);

CREATE VIEW IF NOT EXISTS system_health_latest AS
SELECT *
FROM system_metrics 
WHERE timestamp = (SELECT MAX(timestamp) FROM system_metrics);

-- Performance optimization
ANALYZE;

-- Vacuum to optimize database
VACUUM;