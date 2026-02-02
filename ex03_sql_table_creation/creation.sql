-- ============================================================
-- MODÈLE EN ÉTOILE - NYC TAXI DATA WAREHOUSE (VERSION AMÉLIORÉE)
-- Remplacement dim_datetime par dim_date + dim_time
-- ============================================================

-- Suppression des tables si elles existent
DROP TABLE IF EXISTS fact_trips CASCADE;
DROP TABLE IF EXISTS dim_vendor CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;
DROP TABLE IF EXISTS dim_time CASCADE;
DROP TABLE IF EXISTS dim_location CASCADE;
DROP TABLE IF EXISTS dim_payment CASCADE;
DROP TABLE IF EXISTS dim_rate CASCADE;

-- ============================================================
-- TABLES DE DIMENSION
-- ============================================================

-- Dimension: Fournisseurs de service (Vendors)
CREATE TABLE dim_vendor (
    vendor_key SERIAL PRIMARY KEY,
    vendor_id INTEGER NOT NULL UNIQUE,
    vendor_name VARCHAR(100) NOT NULL,
    CONSTRAINT chk_vendor_id CHECK (vendor_id IN (1, 2, 6, 7))
);

-- Dimension: Date (grain = jour)
CREATE TABLE dim_date (
    date_key SERIAL PRIMARY KEY,
    date_value DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,     -- 0..6
    day_name VARCHAR(10) NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    quarter INTEGER NOT NULL,
    CONSTRAINT chk_month CHECK (month BETWEEN 1 AND 12),
    CONSTRAINT chk_day CHECK (day BETWEEN 1 AND 31),
    CONSTRAINT chk_day_of_week CHECK (day_of_week BETWEEN 0 AND 6),
    CONSTRAINT chk_quarter CHECK (quarter BETWEEN 1 AND 4)
);

CREATE INDEX idx_date_value ON dim_date(date_value);
CREATE INDEX idx_date_year_month ON dim_date(year, month);

-- Dimension: Temps (grain = minute)
CREATE TABLE dim_time (
    time_key SERIAL PRIMARY KEY,
    hour INTEGER NOT NULL,
    minute INTEGER NOT NULL,
    time_value TIME NOT NULL UNIQUE,  -- ex: 13:42:00 (secondes à 00)
    CONSTRAINT chk_hour CHECK (hour BETWEEN 0 AND 23),
    CONSTRAINT chk_minute CHECK (minute BETWEEN 0 AND 59)
);

CREATE INDEX idx_time_hour ON dim_time(hour);

-- Dimension: Localisation (TLC Taxi Zones)
CREATE TABLE dim_location (
    location_key SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL UNIQUE,
    borough VARCHAR(50),
    zone VARCHAR(100),
    service_zone VARCHAR(50),
    CONSTRAINT chk_location_id CHECK (location_id > 0)
);

-- Dimension: Type de paiement
CREATE TABLE dim_payment (
    payment_key SERIAL PRIMARY KEY,
    payment_type INTEGER NOT NULL UNIQUE,
    payment_description VARCHAR(50) NOT NULL,
    CONSTRAINT chk_payment_type CHECK (payment_type BETWEEN 0 AND 6)
);

-- Dimension: Code tarifaire
CREATE TABLE dim_rate (
    rate_key SERIAL PRIMARY KEY,
    rate_code_id INTEGER NOT NULL UNIQUE,
    rate_description VARCHAR(50) NOT NULL,
    CONSTRAINT chk_rate_code CHECK (rate_code_id IN (1, 2, 3, 4, 5, 6, 99))
);

-- ============================================================
-- TABLE DE FAIT
-- ============================================================

CREATE TABLE fact_trips (
    trip_key BIGSERIAL PRIMARY KEY,

    -- Clés étrangères vers les dimensions
    vendor_key INTEGER NOT NULL,

    -- Pickup : date + time
    pickup_date_key INTEGER NOT NULL,
    pickup_time_key INTEGER NOT NULL,

    -- Dropoff : date + time
    dropoff_date_key INTEGER NOT NULL,
    dropoff_time_key INTEGER NOT NULL,

    pickup_location_key INTEGER NOT NULL,
    dropoff_location_key INTEGER NOT NULL,
    payment_key INTEGER NOT NULL,
    rate_key INTEGER NOT NULL,

    -- Mesures (metrics)
    passenger_count INTEGER,
    trip_distance DECIMAL(10, 2),
    trip_duration_minutes INTEGER,

    -- Montants financiers
    fare_amount DECIMAL(10, 2),
    extra DECIMAL(10, 2),
    mta_tax DECIMAL(10, 2),
    tip_amount DECIMAL(10, 2),
    tolls_amount DECIMAL(10, 2),
    improvement_surcharge DECIMAL(10, 2),
    total_amount DECIMAL(10, 2),
    congestion_surcharge DECIMAL(10, 2),
    airport_fee DECIMAL(10, 2),
    cbd_congestion_fee DECIMAL(10, 2),

    -- Indicateurs
    store_and_fwd_flag CHAR(1),

    -- Contraintes de clés étrangères
    CONSTRAINT fk_vendor FOREIGN KEY (vendor_key)
        REFERENCES dim_vendor(vendor_key),

    CONSTRAINT fk_pickup_date FOREIGN KEY (pickup_date_key)
        REFERENCES dim_date(date_key),
    CONSTRAINT fk_pickup_time FOREIGN KEY (pickup_time_key)
        REFERENCES dim_time(time_key),

    CONSTRAINT fk_dropoff_date FOREIGN KEY (dropoff_date_key)
        REFERENCES dim_date(date_key),
    CONSTRAINT fk_dropoff_time FOREIGN KEY (dropoff_time_key)
        REFERENCES dim_time(time_key),

    CONSTRAINT fk_pickup_location FOREIGN KEY (pickup_location_key)
        REFERENCES dim_location(location_key),
    CONSTRAINT fk_dropoff_location FOREIGN KEY (dropoff_location_key)
        REFERENCES dim_location(location_key),
    CONSTRAINT fk_payment FOREIGN KEY (payment_key)
        REFERENCES dim_payment(payment_key),
    CONSTRAINT fk_rate FOREIGN KEY (rate_key)
        REFERENCES dim_rate(rate_key),

    -- Contraintes métier
    CONSTRAINT chk_passenger_count CHECK (passenger_count >= 0 AND passenger_count <= 9),
    CONSTRAINT chk_trip_distance CHECK (trip_distance >= 0),
    CONSTRAINT chk_trip_duration CHECK (trip_duration_minutes >= 0),
    CONSTRAINT chk_fare_amount CHECK (fare_amount >= 0),
    CONSTRAINT chk_total_amount CHECK (total_amount >= 0),
    CONSTRAINT chk_store_fwd CHECK (store_and_fwd_flag IN ('Y', 'N'))
);

-- Index pour optimiser les requêtes analytiques
CREATE INDEX idx_fact_pickup_date ON fact_trips(pickup_date_key);
CREATE INDEX idx_fact_pickup_time ON fact_trips(pickup_time_key);
CREATE INDEX idx_fact_dropoff_date ON fact_trips(dropoff_date_key);
CREATE INDEX idx_fact_dropoff_time ON fact_trips(dropoff_time_key);

CREATE INDEX idx_fact_pickup_location ON fact_trips(pickup_location_key);
CREATE INDEX idx_fact_dropoff_location ON fact_trips(dropoff_location_key);
CREATE INDEX idx_fact_vendor ON fact_trips(vendor_key);
CREATE INDEX idx_fact_payment ON fact_trips(payment_key);
CREATE INDEX idx_fact_rate ON fact_trips(rate_key);

-- Index composite (analyses fréquentes)
CREATE INDEX idx_fact_temporal ON fact_trips(pickup_date_key, pickup_time_key, vendor_key);
CREATE INDEX idx_fact_geographic ON fact_trips(pickup_location_key, dropoff_location_key);
