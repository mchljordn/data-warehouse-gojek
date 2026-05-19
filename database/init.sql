-- Buat Tabel Dimensi
CREATE TABLE dim_customer (
    customer_id VARCHAR(50) PRIMARY KEY,
    gender VARCHAR(20),
    age_group VARCHAR(30),
    join_date DATE,
    city VARCHAR(100)
);

CREATE TABLE dim_driver (
    driver_id VARCHAR(50) PRIMARY KEY,
    vehicle_type VARCHAR(20),
    driver_rating DECIMAL(3,2),
    driver_status VARCHAR(20)
);

CREATE TABLE dim_service (
    service_id VARCHAR(50) PRIMARY KEY,
    service_name VARCHAR(100)
);

CREATE TABLE dim_time (
    time_id VARCHAR(50) PRIMARY KEY,
    "date" DATE,
    "month" INT,
    quarter INT,
    "year" INT,
    "hour" INT
);

CREATE TABLE dim_location (
    location_id VARCHAR(50) PRIMARY KEY,
    city VARCHAR(100),
    province VARCHAR(100),
    region VARCHAR(100)
);

CREATE TABLE dim_payment (
    payment_id VARCHAR(50) PRIMARY KEY,
    payment_method VARCHAR(100)
);

-- Buat Tabel Fakta
CREATE TABLE Fact_Order (
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