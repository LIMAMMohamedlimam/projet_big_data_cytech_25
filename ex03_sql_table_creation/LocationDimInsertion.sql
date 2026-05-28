-- ============================================================
-- DIM_LOCATION: Zones TLC de New York
-- ============================================================
\copy dim_location(location_id, borough, zone, service_zone) FROM 'ex03_sql_table_creation/data/taxi_zone_lookup.csv' WITH (FORMAT csv, HEADER true)



