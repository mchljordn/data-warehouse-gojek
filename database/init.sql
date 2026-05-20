CREATE SCHEMA IF NOT EXISTS dwh;

SET search_path TO dwh;

-- Buat Tabel Dimensi
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id VARCHAR(50) PRIMARY KEY,
    gender VARCHAR(20),
    age_group VARCHAR(30),
    join_date DATE,
    city VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dim_driver (
    driver_id VARCHAR(50) PRIMARY KEY,
    vehicle_type VARCHAR(20),
    driver_rating DECIMAL(3,2),
    driver_status VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS dim_service (
    service_id VARCHAR(50) PRIMARY KEY,
    service_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dim_time (
    time_id VARCHAR(50) PRIMARY KEY,
    "date" DATE,
    "month" INT,
    quarter INT,
    "year" INT,
    "hour" INT
);

CREATE TABLE IF NOT EXISTS dim_location (
    location_id VARCHAR(50) PRIMARY KEY,
    city VARCHAR(100),
    province VARCHAR(100),
    region VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dim_payment (
    payment_id VARCHAR(50) PRIMARY KEY,
    payment_method VARCHAR(100)
);

-- Buat Tabel Fakta
CREATE TABLE IF NOT EXISTS fact_order (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) REFERENCES dim_customer(customer_id),
    driver_id VARCHAR(50) REFERENCES dim_driver(driver_id),
    service_id VARCHAR(50) REFERENCES dim_service(service_id),
    payment_id VARCHAR(50) REFERENCES dim_payment(payment_id),
    location_id VARCHAR(50) REFERENCES dim_location(location_id),
    time_id VARCHAR(50) REFERENCES dim_time(time_id),
    price DECIMAL(12,2),
    distance DECIMAL(6,2),
    discount DECIMAL(12,2),
    order_status VARCHAR(50)
);

-- Seed dim_time untuk 1 Jan 2023 s.d. 31 Des 2024 per jam
INSERT INTO dim_time (time_id, "date", "month", quarter, "year", "hour")
SELECT 
    TO_CHAR(ts, 'YYYYMMDDHH24') AS time_id,
    DATE(ts) AS "date",
    EXTRACT(MONTH FROM ts) AS "month",
    EXTRACT(QUARTER FROM ts) AS quarter,
    EXTRACT(YEAR FROM ts) AS "year",
    EXTRACT(HOUR FROM ts) AS "hour"
FROM generate_series(
    '2023-01-01 00:00:00'::timestamp,
    '2024-12-31 23:00:00'::timestamp,
    '1 hour'::interval
) AS ts
ON CONFLICT (time_id) DO NOTHING;