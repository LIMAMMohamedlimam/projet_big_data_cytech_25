# NYC Yellow Taxi — End-to-End Big Data Pipeline

> Academic project built at **CY Tech (2025–2026)** under the supervision of [Rakib SHEIKH](https://github.com/Noobzik).  
> A full production-style data pipeline — from raw file ingestion to an interactive analytics dashboard and a deployed ML prediction service.

---

## Overview

This project implements a complete, reproducible big data pipeline on **NYC Yellow Taxi trip records**.  
It covers every stage of the data engineering & data science lifecycle:

```
NYC TLC (Parquet) ──► Spark Ingestion ──► Data Cleaning ──► PostgreSQL DWH ──► Dashboard + ML Service
```

The entire infrastructure runs locally via **Docker Compose** (Spark cluster + MinIO S3 + PostgreSQL).

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Docker Compose                            │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────────────┐ │
│  │ Spark Master│◄──►│ Spark Worker│    │   MinIO (S3)         │ │
│  │  :8081      │    │  × 2        │    │   nyc-raw / cleaned  │ │
│  └─────────────┘    └─────────────┘    └──────────────────────┘ │
│                                                                  │
│  ┌───────────────────┐    ┌──────────────────────────────────┐  │
│  │  PostgreSQL :5432 │    │  pgAdmin :5050                   │  │
│  │  nyc_taxi_pro_    │    │  (DWH inspection)                │  │
│  │  big_data         │    └──────────────────────────────────┘  │
│  └───────────────────┘                                           │
└──────────────────────────────────────────────────────────────────┘
```

| Service | Image | Port |
|---|---|---|
| Spark Master | Custom Dockerfile (Spark 3.5.5 / Scala 2.13) | 8081 (UI), 7077 |
| Spark Worker ×2 | Same image — 2 GB / 2 cores each | — |
| MinIO | `minio/minio` | 9000 (S3 API), 9001 (Console) |
| PostgreSQL | `postgres:16` | 5432 |
| pgAdmin | `dpage/pgadmin4` | 5050 |

---

## Pipeline Stages

### 1 · Data Retrieval — `ex01_data_retrieval/` (Scala / Spark)

Downloads NYC TLC Parquet files from the public API and streams them directly into MinIO without intermediate disk buffering.

- Uses Java `HttpClient` + MinIO SDK for zero-copy streaming upload
- Spark configured with S3A connector for subsequent reads
- Output: raw Parquet in `s3a://nyc-raw/`

**Stack:** Scala 2.13, Apache Spark 3.5.5, MinIO SDK 8.5.7, Hadoop-AWS 3.3.4

---

### 2 · Data Ingestion & Cleaning — `ex02_data_ingestion/` (Scala / Spark)

Two-branch Spark pipeline that validates and transforms raw trip data:

**Branch 1 — Validation & Cleaning (Bronze → Silver)**

Strict NYC TLC contract enforcement:
- Valid `VendorID` (1, 2, 6, 7)
- Chronologically consistent pickup/dropoff timestamps
- Passenger count 0–9, trip distance 0–200 mi, fare 0–$1000
- `total_amount` coherence check (component sum within $0.50 tolerance)
- Output: cleaned Parquet in `s3a://nyc-cleaned/`

**Branch 2 — Dimension Enrichment (Silver → Gold / PostgreSQL)**

Star-schema enrichment with Spark UDFs and broadcast joins:
- Lookup surrogate keys for vendor, payment, rate code, location, date, time dimensions
- Computes `trip_duration_minutes`
- Batch-inserts enriched rows into `fact_trips` via JDBC

**Stack:** Scala 2.13, Apache Spark 3.5.5, PostgreSQL JDBC

---

### 3 · Data Warehouse — `ex03_sql_table_creation/` (SQL / PostgreSQL)

Star-schema data model optimised for analytical queries:

```
                  dim_vendor       dim_payment      dim_rate
                      │                │               │
dim_date ─────────────┤                │               │
dim_time ─────────────┼──── fact_trips ┼───────────────┘
dim_location ─────────┤    (BIGSERIAL) │
                       └───────────────┘
```

**Dimension tables:** `dim_vendor`, `dim_date` (day grain), `dim_time` (minute grain), `dim_location` (TLC taxi zones), `dim_payment`, `dim_rate`

**Fact table:** `fact_trips` with 20+ financial and operational measures, full FK constraints, and composite indexes on temporal and geographic keys for fast analytics.

---

### 4 · Analytics Dashboard — `ex04_dashboard/` (Python / Streamlit)

Interactive dashboard connected live to PostgreSQL with date-range and hourly filters.

**KPIs displayed:**
- Total trips, total revenue, average fare, average distance, average duration

**Visualisations:**
- Revenue by day of week (bar chart)
- Trip volume by hour of day (line chart)
- Top 10 pickup zones (horizontal bar, coloured by borough)
- Borough distribution (donut chart)
- Revenue by payment type
- Volume & average fare by vendor (dual-axis bar)

**Stack:** Python, Streamlit, Plotly, pandas, psycopg2

**Dashboard preview:**

| | |
|---|---|
| ![KPIs](rapport/dashboard_scrnshts/Screenshot%20from%202026-02-13%2001-53-59.png) | ![Temporal](rapport/dashboard_scrnshts/Screenshot%20from%202026-02-13%2001-59-19.png) |
| ![Geographic](rapport/dashboard_scrnshts/Screenshot%20from%202026-02-13%2001-59-28.png) | ![Financial](rapport/dashboard_scrnshts/Screenshot%20from%202026-02-13%2001-59-31.png) |

---

### 5 · ML Prediction Service — `ex05_ml_prediction_service/` (Python / scikit-learn)

Batch inference service that predicts `total_amount` for NYC taxi trips.

**Model:** `HistGradientBoostingRegressor` (max_depth=8, lr=0.08, 300 iterations)

**Feature engineering (`src/features.py`):**
- Temporal features from `tpep_pickup_datetime` (hour, day of week, month)
- `trip_duration_min` derived from pickup/dropoff timestamps
- Categorical encoding: `VendorID`, `RatecodeID`, `payment_type`, `store_and_fwd_flag`
- Location IDs as categorical features

**Evaluation results (`artifacts/metrics.json`):**
```json
{ "rmse": 6.31, "n_train": 8000, "n_test": 2000 }
```

**I/O (`src/io_minio.py`):** Reads from and writes to local paths **or** S3/MinIO URIs (`s3://...`) transparently via `s3fs`.

**Input formats supported:** `.parquet`, `.csv`, `.json`, `.jsonl`  
**Output:** original columns + `pred_total_amount`

**Usage:**
```bash
# Train
uv run src.train --data s3://nyc-cleaned/yellow_tripdata.parquet --max-rows 300000

# Predict (batch)
uv run src.predict --input sample.csv --output predictions.csv
```

**Stack:** Python 3.12, scikit-learn 1.8, pandas 3.0, joblib, s3fs, boto3, pytest

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Java 11+ / SBT (for Scala exercises)
- [uv](https://docs.astral.sh/uv/) >= 0.9.26 (for Python exercises)

### Start the infrastructure

```bash
docker compose up -d
```

| Service | URL | Credentials |
|---|---|---|
| Spark UI | http://localhost:8081 | — |
| MinIO Console | http://localhost:9001 | `minio` / `minio123` |
| pgAdmin | http://localhost:5050 | `admin@example.com` / `admin123` |

### Run the Scala pipeline (ex01 + ex02)

```bash
cd ex01_data_retrieval && sbt run
cd ../ex02_data_ingestion && sbt run
```

### Initialise the data warehouse (ex03)

```bash
psql -h localhost -p 5432 -U admin -d nyc_taxi_pro_big_data \
     -f ex03_sql_table_creation/creation.sql
psql -h localhost -p 5432 -U admin -d nyc_taxi_pro_big_data \
     -f ex03_sql_table_creation/insertion.sql
```

### Launch the dashboard (ex04)

```bash
cd ex04_dashboard
python -m venv venv && source venv/bin/activate
pip install -r requirement.txt
streamlit run streamlit_app.py
```

### Train the ML model and run predictions (ex05)

```bash
cd ex05_ml_prediction_service
uv venv && uv pip install -r requirements.txt

# Train
uv run src.train --data ../yellow_tripdata_cleaned_2024-01.parquet

# Predict
uv run src.predict --input sample.csv --output predictions.csv
```

### Stop the infrastructure

```bash
docker compose down
```

---

## Repository Structure

```
.
├── docker-compose.yml          # Full infrastructure (Spark, MinIO, PostgreSQL, pgAdmin)
├── Docker/
│   └── Dockerfile              # Custom Spark 3.5.5 + Scala 2.13 image
├── ex01_data_retrieval/        # Scala/Spark — Download & stream to MinIO
├── ex02_data_ingestion/        # Scala/Spark — Clean + load to PostgreSQL
├── ex03_sql_table_creation/    # SQL — Star-schema DDL + dimension seeding
├── ex04_dashboard/             # Python/Streamlit — Interactive analytics dashboard
├── ex05_ml_prediction_service/ # Python/scikit-learn — ML training & batch inference
│   ├── src/                    # train, predict, features, validate, io_minio
│   ├── tests/                  # pytest — input validation tests
│   └── artifacts/              # Serialised model, metrics, schema
└── rapport/                    # Project report + dashboard screenshots
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Distributed compute | Apache Spark 3.5.5 |
| Language (pipeline) | Scala 2.13 |
| Language (analytics & ML) | Python 3.12 |
| Object storage | MinIO (S3-compatible) |
| Data warehouse | PostgreSQL 16 — star schema |
| Dashboard | Streamlit + Plotly |
| ML | scikit-learn 1.8 (HistGradientBoosting) |
| Containerisation | Docker Compose |
| Dependency management | SBT (Scala), uv (Python) |

---

## Author

**Mohamed LIMAM** — GitHub: [LIMAMMohamedlimam](https://github.com/LIMAMMohamedlimam)

> Project supervised by **Rakib SHEIKH** — GitHub: [Noobzik](https://github.com/Noobzik)  
> CY Tech — Big Data 2025–2026
