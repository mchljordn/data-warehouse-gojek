-- =============================================================================
-- Gojek DWH — Materialized Views for Dashboard Query Optimization
-- Run once after ETL completes. Refresh daily/hourly as needed.
-- =============================================================================

SET search_path TO dwh;

-- ─── 1. Revenue by Service (refreshed daily) ─────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_revenue_by_service AS
SELECT
    s.service_name,
    COUNT(f.order_id)                           AS total_orders,
    SUM(f.price)                                AS total_revenue,
    ROUND(AVG(f.price)::numeric, 0)             AS avg_price,
    SUM(CASE WHEN f.order_status = 'completed' THEN 1 ELSE 0 END) AS completed_orders,
    SUM(CASE WHEN f.order_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders
FROM fact_order f
JOIN dim_service s ON f.service_id = s.service_id
GROUP BY s.service_name
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_revenue_service
    ON mv_revenue_by_service (service_name);


-- ─── 2. Monthly Revenue Trend ────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_monthly_revenue AS
SELECT
    t.year,
    t.month,
    TO_DATE(t.year::text || '-' || LPAD(t.month::text, 2, '0') || '-01', 'YYYY-MM-DD') AS period,
    s.service_name,
    COUNT(f.order_id)   AS total_orders,
    SUM(f.price)        AS total_revenue,
    SUM(f.discount)     AS total_discount
FROM fact_order f
JOIN dim_time    t ON f.time_id    = t.time_id
JOIN dim_service s ON f.service_id = s.service_id
GROUP BY t.year, t.month, s.service_name
WITH DATA;

CREATE INDEX IF NOT EXISTS idx_mv_monthly_period
    ON mv_monthly_revenue (period);


-- ─── 3. Driver Performance Summary ──────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_driver_performance AS
SELECT
    f.driver_id,
    d.vehicle_type,
    d.driver_status,
    d.driver_rating,
    COUNT(f.order_id)   AS total_orders,
    SUM(f.price)        AS total_revenue,
    ROUND(AVG(f.distance)::numeric, 2) AS avg_distance,
    SUM(CASE WHEN f.order_status = 'completed' THEN 1 ELSE 0 END) AS completed_orders,
    SUM(CASE WHEN f.order_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders
FROM fact_order f
JOIN dim_driver d ON f.driver_id = d.driver_id
GROUP BY f.driver_id, d.vehicle_type, d.driver_status, d.driver_rating
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_driver_id
    ON mv_driver_performance (driver_id);

CREATE INDEX IF NOT EXISTS idx_mv_driver_vehicle
    ON mv_driver_performance (vehicle_type);


-- ─── 4. Peak Hour Aggregation ────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_peak_hour AS
SELECT
    TO_CHAR(t.date, 'Dy')   AS day_of_week,
    TO_CHAR(t.date, 'D')::int AS dow_num,
    t.hour,
    COUNT(f.order_id)        AS total_orders,
    SUM(f.price)             AS total_revenue
FROM fact_order f
JOIN dim_time t ON f.time_id = t.time_id
GROUP BY day_of_week, dow_num, t.hour
WITH DATA;

CREATE INDEX IF NOT EXISTS idx_mv_peak_hour
    ON mv_peak_hour (hour);


-- ─── 5. City/Region Revenue Summary ─────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_city_revenue AS
SELECT
    l.city,
    l.province,
    l.region,
    COUNT(f.order_id)   AS total_orders,
    SUM(f.price)        AS total_revenue,
    ROUND(AVG(f.price)::numeric, 0) AS avg_price,
    ROUND(
        100.0 * SUM(CASE WHEN f.order_status = 'cancelled' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 2
    )                   AS cancellation_rate_pct
FROM fact_order f
JOIN dim_location l ON f.location_id = l.location_id
GROUP BY l.city, l.province, l.region
WITH DATA;

CREATE INDEX IF NOT EXISTS idx_mv_city_region
    ON mv_city_revenue (region, province);


-- =============================================================================
-- Refresh Commands (run via cron or pg_cron)
-- =============================================================================
-- REFRESH MATERIALIZED VIEW CONCURRENTLY dwh.mv_revenue_by_service;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY dwh.mv_monthly_revenue;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY dwh.mv_driver_performance;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY dwh.mv_peak_hour;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY dwh.mv_city_revenue;


-- =============================================================================
-- Performance Indexes on Fact Table
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_fact_order_service
    ON dwh.fact_order (service_id);

CREATE INDEX IF NOT EXISTS idx_fact_order_driver
    ON dwh.fact_order (driver_id);

CREATE INDEX IF NOT EXISTS idx_fact_order_time
    ON dwh.fact_order (time_id);

CREATE INDEX IF NOT EXISTS idx_fact_order_location
    ON dwh.fact_order (location_id);

CREATE INDEX IF NOT EXISTS idx_fact_order_status
    ON dwh.fact_order (order_status);

-- Composite index for common filter combos
CREATE INDEX IF NOT EXISTS idx_fact_order_status_service
    ON dwh.fact_order (order_status, service_id);
