"""
OLAP Query Library for GoGrab DWH Dashboard.
All queries target the dwh schema in PostgreSQL.
"""

def _build_where_clause(**filters) -> str:
    """Build dynamic WHERE clause based on sidebar filter selections."""
    conditions = []
    
    years = filters.get('years')
    regions = filters.get('regions')
    services = filters.get('services')
    cities = filters.get('cities')
    vehicle_types = filters.get('vehicle_types')
    payment_methods = filters.get('payment_methods')
    
    if years:
        formatted_years = ", ".join([f"'{y}'" for y in years])
        conditions.append(f"t.year::text IN ({formatted_years})")
        
    if regions:
        formatted_regions = ", ".join([f"'{r.lower()}'" for r in regions])
        conditions.append(f"LOWER(l.region) IN ({formatted_regions})")
        
    if services:
        formatted_services = ", ".join([f"'{s.lower()}'" for s in services])
        conditions.append(f"LOWER(s.service_name) IN ({formatted_services})")
        
    if cities:
        formatted_cities = ", ".join([f"'{c.lower()}'" for c in cities])
        conditions.append(f"LOWER(l.city) IN ({formatted_cities})")
        
    if vehicle_types:
        formatted_vehicles = ", ".join([f"'{v.lower()}'" for v in vehicle_types])
        # Note: Depending on the query, dim_driver might not be joined. We assume it is if vehicle_types is filtered.
        # Actually, to be safe, we only filter driver if dim_driver is present or through fact_order if we need to.
        # But dim_driver is joined in driver analytics. For revenue, it isn't. So if vehicle_types is used, we need to join dim_driver in the base query.
        # Since these are global filters, this is tricky! 
        # For simplicity, if we add these, we must ensure all queries join the needed tables, OR we filter via subqueries.
        # Filtering via subquery is safer since we don't know if the main query joins dim_driver or dim_payment!
        conditions.append(f"f.driver_id IN (SELECT driver_id FROM dwh.dim_driver WHERE LOWER(vehicle_type) IN ({formatted_vehicles}))")

    if payment_methods:
        formatted_payments = ", ".join([f"'{p.lower()}'" for p in payment_methods])
        conditions.append(f"f.payment_id IN (SELECT payment_id FROM dwh.dim_payment WHERE LOWER(payment_method) IN ({formatted_payments}))")
        
    return "WHERE " + " AND ".join(conditions) if conditions else ""


# --- KPI SUMMARY METRICS ---

def q_kpi_summary(**filters) -> str:
    """Fetch high-level KPI cards metrics (orders, revenue, averages, cancellations)."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        COUNT(f.order_id)                                                                   AS total_orders,
        COALESCE(SUM(f.price), 0)                                                           AS total_revenue,
        COALESCE(SUM(f.net_revenue), 0)                                                     AS total_net_revenue,
        ROUND(COALESCE(AVG(f.price), 0)::numeric, 0)                                        AS avg_order_value,
        ROUND(COALESCE(SUM(f.discount), 0)::numeric, 0)                                     AS total_discount,
        ROUND(COALESCE(AVG(f.distance), 0)::numeric, 2)                                     AS avg_distance_km,
        ROUND(
            100.0 * SUM(CASE WHEN f.order_status = 'cancelled' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(f.order_id), 0), 2
        )                                                                                   AS cancellation_rate_pct,
        COUNT(DISTINCT f.customer_id)                                                       AS unique_customers,
        COUNT(DISTINCT f.driver_id)                                                         AS active_drivers
    FROM dwh.fact_order f
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause};
    """


# --- REVENUE & SERVICE ANALYTICS ---

def q_revenue_by_service(**filters) -> str:
    """Get total revenue and order volume by service type."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        s.service_name,
        COUNT(f.order_id)                                           AS total_orders,
        SUM(f.price)                                                AS total_revenue,
        ROUND(AVG(f.price)::numeric, 0)                             AS avg_price,
        ROUND(
            100.0 * SUM(f.price) / SUM(SUM(f.price)) OVER (), 2
        )                                                           AS revenue_share_pct
    FROM dwh.fact_order f
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    {where_clause}
    GROUP BY s.service_name
    ORDER BY total_revenue DESC;
    """


def q_revenue_monthly_trend(**filters) -> str:
    """Calculate monthly revenue trends and Month-over-Month growth."""
    where_clause = _build_where_clause(**filters)
    return f"""
    WITH monthly AS (
        SELECT
            t.year,
            t.month,
            TO_DATE(t.year::text || '-' || LPAD(t.month::text, 2, '0') || '-01', 'YYYY-MM-DD') AS period,
            SUM(f.price)    AS revenue,
            COUNT(f.order_id) AS orders
        FROM dwh.fact_order f
        JOIN dwh.dim_time t ON f.time_id = t.time_id
        JOIN dwh.dim_location l ON f.location_id = l.location_id
        JOIN dwh.dim_service s ON f.service_id = s.service_id
        {where_clause}
        GROUP BY t.year, t.month
    )
    SELECT
        period,
        year,
        month,
        revenue,
        orders,
        ROUND(
            100.0 * (revenue - LAG(revenue) OVER (ORDER BY period))
            / NULLIF(LAG(revenue) OVER (ORDER BY period), 0), 2
        ) AS mom_growth_pct
    FROM monthly
    ORDER BY period;
    """


def q_revenue_by_region(**filters) -> str:
    """Aggregate revenue by region, province, and city using ROLLUP."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        CASE WHEN GROUPING(l.region) = 1 THEN 'ALL REGIONS' ELSE l.region END     AS region,
        CASE WHEN GROUPING(l.province) = 1 THEN 'ALL PROVINCES' ELSE l.province END AS province,
        CASE WHEN GROUPING(l.city) = 1 THEN 'ALL CITIES' ELSE l.city END         AS city,
        COUNT(f.order_id)   AS total_orders,
        SUM(f.price)        AS total_revenue,
        ROUND(AVG(f.price)::numeric, 0) AS avg_price
    FROM dwh.fact_order f
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY ROLLUP(l.region, l.province, l.city)
    ORDER BY GROUPING(l.region), l.region, 
             GROUPING(l.province), l.province, 
             GROUPING(l.city), total_revenue DESC;
    """


def q_top_cities_revenue(limit: int = 250, **filters) -> str:
    """Retrieve top cities based on total revenue generation."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        l.city,
        l.province,
        l.region,
        COUNT(f.order_id)                                   AS total_orders,
        SUM(f.price)                                        AS total_revenue,
        ROUND(AVG(f.price)::numeric, 0)                     AS avg_price,
        ROUND(
            100.0 * SUM(CASE WHEN f.order_status = 'cancelled' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0), 2
        )                                                   AS cancellation_rate_pct
    FROM dwh.fact_order f
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY l.city, l.province, l.region
    ORDER BY total_revenue DESC
    LIMIT {limit};
    """


# --- DEMAND & TIME ANALYSIS ---

def q_peak_hour_heatmap(**filters) -> str:
    """Fetch order volume count mapped by day-of-week and hour."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        TO_CHAR(t.date, 'D')::int                                   AS dow_num,
        TO_CHAR(t.date, 'Dy')                                       AS day_of_week,
        t.hour,
        COUNT(f.order_id)                                           AS total_orders,
        SUM(f.price)                                                AS total_revenue,
        ROUND(AVG(f.price)::numeric, 0)                             AS avg_price
    FROM dwh.fact_order f
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY dow_num, day_of_week, t.hour
    ORDER BY dow_num, t.hour;
    """


def q_orders_by_hour(**filters) -> str:
    """Get hourly distribution of orders and revenues."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        t.hour,
        COUNT(f.order_id)                                           AS total_orders,
        SUM(f.price)                                                AS total_revenue,
        ROUND(AVG(f.price)::numeric, 0)                             AS avg_price,
        ROUND(
            100.0 * COUNT(f.order_id) / SUM(COUNT(f.order_id)) OVER (), 2
        )                                                           AS order_share_pct
    FROM dwh.fact_order f
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY t.hour
    ORDER BY t.hour;
    """


def q_time_of_day_segmentation(**filters) -> str:
    """Segment orders by time of day blocks."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        CASE
            WHEN t.hour BETWEEN 5 AND 9 THEN '1. Morning Rush (05-09)'
            WHEN t.hour BETWEEN 10 AND 14 THEN '2. Mid-day & Lunch (10-14)'
            WHEN t.hour BETWEEN 15 AND 19 THEN '3. Evening Rush (15-19)'
            WHEN t.hour BETWEEN 20 AND 23 THEN '4. Night (20-23)'
            ELSE '5. Midnight (00-04)'
        END AS time_of_day,
        COUNT(f.order_id)                                           AS total_orders,
        SUM(f.price)                                                AS total_revenue,
        ROUND(AVG(f.price)::numeric, 0)                             AS avg_price,
        ROUND(
            100.0 * COUNT(f.order_id) / SUM(COUNT(f.order_id)) OVER (), 2
        )                                                           AS order_share_pct
    FROM dwh.fact_order f
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY time_of_day
    ORDER BY time_of_day;
    """


def q_revenue_by_quarter(**filters) -> str:
    """Aggregate revenue by year and quarter using ROLLUP."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        CASE WHEN GROUPING(t.year) = 1 THEN 'All Years' ELSE t.year::text END       AS year,
        CASE WHEN GROUPING(t.quarter) = 1 THEN 'All Quarters' ELSE t.quarter::text END AS quarter,
        COUNT(f.order_id)   AS total_orders,
        SUM(f.price)        AS total_revenue,
        ROUND(AVG(f.price)::numeric, 0) AS avg_price
    FROM dwh.fact_order f
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY ROLLUP(t.year, t.quarter)
    ORDER BY GROUPING(t.year), t.year, GROUPING(t.quarter), t.quarter;
    """


# --- DRIVER PERFORMANCE ---

def q_driver_performance_summary(**filters) -> str:
    """Summarize driver performance metrics by vehicle type and status."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        d.vehicle_type,
        d.driver_status,
        COUNT(DISTINCT f.driver_id)                 AS driver_count,
        COUNT(f.order_id)                           AS total_orders,
        ROUND(AVG(d.driver_rating)::numeric, 2)     AS avg_rating,
        ROUND(AVG(f.price)::numeric, 0)             AS avg_order_price,
        ROUND(AVG(f.distance)::numeric, 2)          AS avg_distance_km,
        ROUND(
            100.0 * SUM(CASE WHEN f.order_status = 'cancelled' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0), 2
        )                                           AS cancellation_rate_pct,
        SUM(f.price)                                AS total_revenue_generated
    FROM dwh.fact_order f
    JOIN dwh.dim_driver d ON f.driver_id = d.driver_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY d.vehicle_type, d.driver_status
    ORDER BY total_revenue_generated DESC;
    """


def q_driver_rating_distribution(**filters) -> str:
    """Count drivers across defined rating categories by vehicle type."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        d.vehicle_type,
        CASE
            WHEN d.driver_rating >= 4.8 THEN '4.8-5.0 (Elite)'
            WHEN d.driver_rating >= 4.5 THEN '4.5-4.7 (Good)'
            WHEN d.driver_rating >= 4.0 THEN '4.0-4.4 (Average)'
            ELSE                              '< 4.0 (Low)'
        END                                         AS rating_bucket,
        COUNT(DISTINCT d.driver_id)                 AS driver_count,
        ROUND(AVG(d.driver_rating)::numeric, 3)     AS avg_rating
    FROM dwh.dim_driver d
    JOIN dwh.fact_order f ON d.driver_id = f.driver_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY d.vehicle_type, rating_bucket
    ORDER BY d.vehicle_type, avg_rating DESC;
    """


def q_top_drivers(limit: int = 20, **filters) -> str:
    """Retrieve top-performing drivers based on completed orders and revenues."""
    where_clause = _build_where_clause(**filters)
    if where_clause:
        where_clause += " AND d.driver_status = 'aktif'"
    else:
        where_clause = "WHERE d.driver_status = 'aktif'"

    return f"""
    SELECT
        f.driver_id,
        d.vehicle_type,
        d.driver_status,
        ROUND(d.driver_rating::numeric, 2)          AS rating,
        COUNT(f.order_id)                           AS total_orders,
        SUM(CASE WHEN f.order_status = 'completed' THEN 1 ELSE 0 END) AS completed,
        SUM(f.price)                                AS total_revenue,
        ROUND(AVG(f.distance)::numeric, 2)          AS avg_distance_km
    FROM dwh.fact_order f
    JOIN dwh.dim_driver d ON f.driver_id = d.driver_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY f.driver_id, d.vehicle_type, d.driver_status, d.driver_rating
    ORDER BY total_revenue DESC
    LIMIT {limit};
    """


# --- CANCELLATIONS & FAILURES ---

def q_cancellation_by_service(**filters) -> str:
    """Calculate order cancellation rates for each service category."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        s.service_name,
        COUNT(*)                                                    AS total_orders,
        SUM(CASE WHEN f.order_status = 'completed'  THEN 1 ELSE 0 END) AS completed,
        SUM(CASE WHEN f.order_status = 'cancelled'  THEN 1 ELSE 0 END) AS cancelled,
        ROUND(
            100.0 * SUM(CASE WHEN f.order_status = 'cancelled' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0), 2
        )                                                           AS cancellation_rate_pct
    FROM dwh.fact_order f
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    {where_clause}
    GROUP BY s.service_name
    ORDER BY cancellation_rate_pct DESC;
    """


def q_cancellation_by_hour(**filters) -> str:
    """Calculate cancellation rate by hour of the day."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        t.hour,
        COUNT(*)                                                    AS total_orders,
        SUM(CASE WHEN f.order_status = 'cancelled'  THEN 1 ELSE 0 END) AS cancelled,
        ROUND(
            100.0 * SUM(CASE WHEN f.order_status = 'cancelled' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0), 2
        )                                                           AS cancellation_rate_pct
    FROM dwh.fact_order f
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY t.hour
    ORDER BY t.hour;
    """


def q_cancellation_by_region(limit: int = 250, **filters) -> str:
    """Aggregate cancellations by region and province using ROLLUP."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        CASE WHEN GROUPING(l.region) = 1 THEN 'All Regions' ELSE l.region END       AS region,
        CASE WHEN GROUPING(l.province) = 1 THEN 'All Provinces' ELSE l.province END AS province,
        COUNT(*)                                                                    AS total_orders,
        SUM(CASE WHEN f.order_status = 'cancelled' THEN 1 ELSE 0 END)               AS cancelled,
        ROUND(
            100.0 * SUM(CASE WHEN f.order_status = 'cancelled' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0), 2
        )                                                                           AS cancellation_rate_pct
    FROM dwh.fact_order f
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY ROLLUP(l.region, l.province)
    ORDER BY GROUPING(l.region), l.region, GROUPING(l.province), total_orders DESC
    LIMIT {limit};
    """


# --- DISCOUNT EFFECTIVENESS ---

def q_discount_effectiveness(**filters) -> str:
    """Analyze order completion rates across services and discount tiers."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        CASE
            WHEN f.discount = 0        THEN 'No Discount'
            WHEN f.discount <= 5000    THEN 'Rp 1 – 5K'
            ELSE                            'Rp 5K+'
        END                                             AS discount_tier,
        s.service_name,
        COUNT(*)                                        AS total_orders,
        SUM(CASE WHEN f.order_status = 'completed' THEN 1 ELSE 0 END) AS completed,
        ROUND(
            100.0 * SUM(CASE WHEN f.order_status = 'completed' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0), 2
        )                                               AS completion_rate_pct,
        ROUND(AVG(f.price)::numeric, 0)                 AS avg_price,
        ROUND(SUM(f.discount)::numeric, 0)              AS total_discount_given,
        ROUND(SUM(f.price)::numeric, 0)                 AS total_revenue
    FROM dwh.fact_order f
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    {where_clause}
    GROUP BY discount_tier, s.service_name
    ORDER BY discount_tier, s.service_name;
    """


def q_discount_by_age_group(**filters) -> str:
    """Analyze completion rates and discount amounts by customer age group."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        c.age_group,
        CASE
            WHEN f.discount = 0     THEN 'No Discount'
            WHEN f.discount <= 5000 THEN 'Rp 1 – 5K'
            ELSE                         'Rp 5K+'
        END                                             AS discount_tier,
        COUNT(*)                                        AS total_orders,
        ROUND(
            100.0 * SUM(CASE WHEN f.order_status = 'completed' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0), 2
        )                                               AS completion_rate_pct,
        ROUND(SUM(f.discount)::numeric, 0)              AS total_discount,
        ROUND(SUM(f.price)::numeric, 0)                 AS total_revenue
    FROM dwh.fact_order f
    JOIN dwh.dim_customer c ON f.customer_id = c.customer_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY c.age_group, discount_tier
    ORDER BY c.age_group, discount_tier;
    """


# --- CUSTOMER DEMOGRAPHICS ---

def q_customer_age_gender_analysis(**filters) -> str:
    """Perform multi-dimensional analysis on customer age groups and gender using CUBE."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        CASE WHEN GROUPING(c.customer_segment) = 1 THEN '(All Segments)' ELSE c.customer_segment END    AS customer_segment,
        CASE WHEN GROUPING(c.gender) = 1 THEN '(All Genders)' ELSE c.gender END       AS gender,
        COUNT(f.order_id)                                                       AS total_orders,
        SUM(f.price)                                                            AS total_revenue,
        ROUND(AVG(f.price)::numeric, 0)                                         AS avg_order_value,
        ROUND(AVG(f.discount)::numeric, 0)                                      AS avg_discount,
        ROUND(
            100.0 * SUM(CASE WHEN f.order_status = 'cancelled' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0), 2
        )                                                                       AS cancellation_rate_pct
    FROM dwh.fact_order f
    JOIN dwh.dim_customer c ON f.customer_id = c.customer_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY CUBE(c.customer_segment, c.gender)
    ORDER BY GROUPING(c.customer_segment), c.customer_segment, GROUPING(c.gender), c.gender;
    """


def q_payment_method_breakdown(**filters) -> str:
    """Analyze transaction distribution and revenue shares across payment methods."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        p.payment_method,
        COUNT(f.order_id)                                           AS total_orders,
        SUM(f.price)                                                AS total_revenue,
        ROUND(AVG(f.price)::numeric, 0)                             AS avg_price,
        ROUND(
            100.0 * COUNT(f.order_id) / SUM(COUNT(f.order_id)) OVER (), 2
        )                                                           AS order_share_pct,
        ROUND(
            100.0 * SUM(f.price) / SUM(SUM(f.price)) OVER (), 2
        )                                                           AS revenue_share_pct
    FROM dwh.fact_order f
    JOIN dwh.dim_payment p ON f.payment_id = p.payment_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY p.payment_method
    ORDER BY total_revenue DESC;
    """


# --- ADVANCED SEGMENTATION ---

def q_driver_rating_revenue_impact(**filters) -> str:
    """Analyze correlation between Rating Bucket and Revenue."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        CASE
            WHEN d.driver_rating >= 4.8 THEN '4.8–5.0 (Elite)'
            WHEN d.driver_rating >= 4.5 THEN '4.5–4.7 (Good)'
            WHEN d.driver_rating >= 4.0 THEN '4.0–4.4 (Average)'
            ELSE                              '< 4.0 (Low)'
        END                                         AS rating_bucket,
        COUNT(DISTINCT f.driver_id)                 AS driver_count,
        COUNT(f.order_id)                           AS total_orders,
        SUM(f.price)                                AS total_revenue,
        ROUND(AVG(f.price)::numeric, 0)             AS avg_order_value,
        ROUND(SUM(f.price) / NULLIF(COUNT(DISTINCT f.driver_id), 0)::numeric, 0) AS revenue_per_driver
    FROM dwh.dim_driver d
    JOIN dwh.fact_order f ON d.driver_id = f.driver_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY rating_bucket
    ORDER BY total_revenue DESC;
    """

def q_payment_cancellation_rate(**filters) -> str:
    """Compare cancellation rates between Cashless and Cash payments."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        CASE 
            WHEN LOWER(p.payment_method) LIKE '%cash%' AND LOWER(p.payment_method) NOT LIKE '%cashless%' THEN 'Cash'
            ELSE 'Cashless (E-Wallet/CC)'
        END                                                         AS payment_category,
        COUNT(f.order_id)                                           AS total_orders,
        SUM(CASE WHEN f.order_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
        ROUND(
            100.0 * SUM(CASE WHEN f.order_status = 'cancelled' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(f.order_id), 0), 2
        )                                                           AS cancellation_rate_pct,
        SUM(f.price)                                                AS total_revenue
    FROM dwh.fact_order f
    JOIN dwh.dim_payment p ON f.payment_id = p.payment_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY payment_category
    ORDER BY total_orders DESC;
    """

def q_discount_hunter_segmentation(**filters) -> str:
    """Segment users by discount behavior."""
    where_clause = _build_where_clause(**filters)
    return f"""
    WITH customer_behavior AS (
        SELECT 
            f.customer_id,
            COUNT(f.order_id) AS total_orders,
            SUM(CASE WHEN f.discount > 0 THEN 1 ELSE 0 END) AS discount_orders,
            SUM(f.price) AS total_revenue
        FROM dwh.fact_order f
        JOIN dwh.dim_time t ON f.time_id = t.time_id
        JOIN dwh.dim_location l ON f.location_id = l.location_id
        JOIN dwh.dim_service s ON f.service_id = s.service_id
        {where_clause}
        GROUP BY f.customer_id
    )
    SELECT
        CASE 
            WHEN discount_orders::float / NULLIF(total_orders, 0) >= 0.5 THEN 'Discount Hunter'
            ELSE 'Non-Discount User'
        END AS user_behavior,
        COUNT(customer_id) AS user_count,
        SUM(total_orders)  AS total_orders,
        SUM(total_revenue) AS total_revenue,
        ROUND(SUM(total_revenue) / NULLIF(COUNT(customer_id), 0)::numeric, 0) AS avg_revenue_per_user
    FROM customer_behavior
    GROUP BY user_behavior
    ORDER BY total_revenue DESC;
    """

def q_geo_tier_segmentation(**filters) -> str:
    """Compare performance between Java and Non-Java regions."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        CASE 
            WHEN l.region ILIKE '%jawa%' THEN 'Pulau Jawa'
            ELSE 'Luar Jawa'
        END AS geo_tier,
        COUNT(f.order_id)                                           AS total_orders,
        SUM(f.price)                                                AS total_revenue,
        ROUND(AVG(f.price)::numeric, 0)                             AS avg_order_value,
        ROUND(
            100.0 * COUNT(f.order_id) / SUM(COUNT(f.order_id)) OVER (), 2
        )                                                           AS order_share_pct
    FROM dwh.fact_order f
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY geo_tier
    ORDER BY total_revenue DESC;
    """

def q_customer_tenure_segmentation(**filters) -> str:
    """Segment customers by tenure based on join_date."""
    where_clause = _build_where_clause(**filters)
    return f"""
    SELECT
        CASE
            WHEN CURRENT_DATE - c.join_date < 180 THEN '1. New User (< 6 months)'
            WHEN CURRENT_DATE - c.join_date < 365 THEN '2. Regular User (6-12 months)'
            ELSE '3. Loyal User (> 1 year)'
        END AS tenure_segment,
        COUNT(DISTINCT c.customer_id) AS customer_count,
        COUNT(f.order_id) AS total_orders,
        SUM(f.price) AS total_revenue,
        ROUND(SUM(f.price) / NULLIF(COUNT(DISTINCT c.customer_id), 0)::numeric, 0) AS revenue_per_user
    FROM dwh.fact_order f
    JOIN dwh.dim_customer c ON f.customer_id = c.customer_id
    JOIN dwh.dim_time t ON f.time_id = t.time_id
    JOIN dwh.dim_location l ON f.location_id = l.location_id
    JOIN dwh.dim_service s ON f.service_id = s.service_id
    {where_clause}
    GROUP BY tenure_segment
    ORDER BY tenure_segment;
    """

# --- SIDEBAR OPTIONS ---

def q_filter_years() -> str:
    return "SELECT DISTINCT year FROM dwh.dim_time WHERE year IS NOT NULL ORDER BY year;"

def q_filter_regions() -> str:
    return "SELECT DISTINCT region FROM dwh.dim_location WHERE region IS NOT NULL ORDER BY region;"

def q_filter_services() -> str:
    return "SELECT DISTINCT service_name FROM dwh.dim_service WHERE service_name IS NOT NULL ORDER BY service_name;"

def q_filter_cities() -> str:
    return "SELECT DISTINCT city FROM dwh.dim_location WHERE city IS NOT NULL ORDER BY city;"

def q_filter_vehicles() -> str:
    return "SELECT DISTINCT vehicle_type FROM dwh.dim_driver WHERE vehicle_type IS NOT NULL ORDER BY vehicle_type;"

def q_filter_payments() -> str:
    return "SELECT DISTINCT payment_method FROM dwh.dim_payment WHERE payment_method IS NOT NULL ORDER BY payment_method;"
