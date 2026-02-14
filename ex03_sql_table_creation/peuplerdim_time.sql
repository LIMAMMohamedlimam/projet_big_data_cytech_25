-- ============================================================
-- PEUPLER dim_date et dim_time POUR NOVEMBRE 2025 (data set traiter )
-- TODO : modify so it can be used for other months
-- ============================================================

-- Peupler dim_date pour novembre 2025
INSERT INTO dim_date (date_value, year, month, day, day_of_week, day_name, is_weekend, quarter)
SELECT 
    date_value::DATE,
    EXTRACT(YEAR FROM date_value)::INTEGER,
    EXTRACT(MONTH FROM date_value)::INTEGER,
    EXTRACT(DAY FROM date_value)::INTEGER,
    EXTRACT(DOW FROM date_value)::INTEGER,
    TO_CHAR(date_value, 'FMDay'),
    CASE WHEN EXTRACT(DOW FROM date_value) IN (0, 6) THEN TRUE ELSE FALSE END,
    EXTRACT(QUARTER FROM date_value)::INTEGER
FROM generate_series(
    '2025-11-01'::DATE,
    '2025-11-30'::DATE,
    '1 day'::INTERVAL
) AS date_value
ON CONFLICT (date_value) DO NOTHING;



INSERT INTO dim_time (hour, minute, time_value)
SELECT 
    EXTRACT(HOUR FROM ts)::INTEGER,
    EXTRACT(MINUTE FROM ts)::INTEGER,
    ts::TIME
FROM generate_series(
    '2025-11-01 00:00:00'::TIMESTAMP,
    '2025-11-01 23:59:00'::TIMESTAMP,
    '1 minute'::INTERVAL
) AS ts
ON CONFLICT (time_value) DO NOTHING;


