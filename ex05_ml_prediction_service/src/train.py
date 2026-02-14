"""
Training script.

Usage
-----
python -m src.train --data s3://mybucket/yellow.parquet
python -m src.train --data /path/to/file.parquet

Environment variables (for s3://...)
------------------------------------
MINIO_ENDPOINT_URL
MINIO_ACCESS_KEY
MINIO_SECRET_KEY
MINIO_REGION (optional)
"""
from __future__ import annotations

import argparse
import json
import logging
import time

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from .config import get_paths, get_s3_config
from .features import make_features
from .io_minio import read_parquet_any
from .model import build_pipeline
from .validate import DEFAULT_SCHEMA, validate_training_frame


def _select_feature_columns(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Select numeric and categorical columns for the model.

    The function starts from a predefined list of candidate columns and keeps
    only those that are present in the provided dataframe.

    Parameters
    ----------
    df : pandas.DataFrame
        Feature-engineered dataframe.

    Returns
    -------
    numeric : list of str
        Numeric feature column names kept for training.
    categorical : list of str
        Categorical feature column names kept for training.

    Notes
    -----
    This helper is meant to be resilient to missing columns (e.g., depending on
    upstream extraction or feature engineering changes). [web:1]
    """
    numeric = [
        "trip_distance",
        "trip_duration_min",
        "passenger_count",
        "pickup_hour",
        "pickup_dayofweek",
        "pickup_month",
    ]
    categorical = [
        "VendorID",
        "RatecodeID",
        "PULocationID",
        "DOLocationID",
        "store_and_fwd_flag",
        "payment_type",
    ]

    numeric = [c for c in numeric if c in df.columns]
    categorical = [c for c in categorical if c in df.columns]
    return numeric, categorical


def _setup_logging() -> None:
    """Configure logging for CLI output.

    Notes
    -----
    Uses `logging.basicConfig` with an INFO level and a compact format suitable
    for command-line execution. [web:4]
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def _log_step(logger: logging.Logger, name: str):
    """Create a timing context manager for a named pipeline step.

    Parameters
    ----------
    logger : logging.Logger
        Logger used to emit step start/end messages.
    name : str
        Human-readable name of the step.

    Returns
    -------
    timer : object
        An object implementing the context manager protocol (`__enter__`,
        `__exit__`) that logs duration and exceptions.

    Notes
    -----
    Intended usage is `with _log_step(logger, "Step name"):`. [web:4]
    """
    class _Timer:
        def __enter__(self):
            self.t0 = time.perf_counter()
            logger.info("▶ %s ...", name)
            return self

        def __exit__(self, exc_type, exc, tb):
            dt = time.perf_counter() - self.t0
            if exc_type is None:
                logger.info("✅ %s (%.2fs)", name, dt)
            else:
                logger.exception("❌ %s failed after %.2fs", name, dt)

    return _Timer()


def main() -> None:
    """Run the end-to-end training pipeline and save artifacts.

    The pipeline performs:
    - Parquet loading (local path or S3-compatible endpoint),
    - Schema validation,
    - Feature engineering and optional sampling,
    - Train/test split,
    - Model fitting and evaluation (RMSE),
    - Artifact persistence (model, metrics, schema).

    Notes
    -----
    When `--data` starts with `s3://`, S3/MinIO connection parameters are read
    from environment variables and used by the project I/O helpers. [web:4]

    Raises
    ------
    ValueError
        If input data cannot be validated or parsed by underlying helpers.
    FileNotFoundError
        If a local parquet path does not exist (raised by I/O layer).
    KeyError
        If the target column defined by the schema is missing after feature
        engineering.
    """
    _setup_logging()
    logger = logging.getLogger("train")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-rows",
        type=int,
        default=300_000,
        help="Max rows to use for training (sampling). Use 0 for all.",
    )
    parser.add_argument(
        "--data",
        required=True,
        help="Parquet path (local or s3://bucket/key.parquet)",
    )
    parser.add_argument("--test-size", type=float, default=0.2, help="Test split ratio")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    steps = [
        "Load parquet",
        "Validate input",
        "Feature engineering",
        "Split train/test",
        "Fit model",
        "Evaluate",
        "Save artifacts",
    ]

    with tqdm(total=len(steps), desc="Training progress", unit="step") as pbar:
        with _log_step(logger, "Load parquet"):
            s3 = get_s3_config() if args.data.startswith("s3://") else None
            df = read_parquet_any(args.data, s3=s3)
            logger.info("Loaded dataframe: %d rows, %d cols", df.shape[0], df.shape[1])
        pbar.update(1)

        with _log_step(logger, "Validate input"):
            validate_training_frame(df, schema=DEFAULT_SCHEMA)
        pbar.update(1)

        with _log_step(logger, "Feature engineering"):
            df_feat = make_features(df)
            if args.max_rows and args.max_rows > 0 and len(df_feat) > args.max_rows:
                df_feat = df_feat.sample(n=args.max_rows, random_state=args.seed)
                logger.info("Sampled to %d rows for faster training", len(df_feat))
        pbar.update(1)

        with _log_step(logger, "Split train/test"):
            target = DEFAULT_SCHEMA.target
            y = df_feat[target].astype(float)
            X = df_feat.drop(columns=[target])

            numeric_cols, categorical_cols = _select_feature_columns(df_feat)
            keep_cols = numeric_cols + categorical_cols
            X = X[keep_cols].copy()

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=args.test_size, random_state=args.seed
            )
            logger.info("Train: %d rows | Test: %d rows", len(X_train), len(X_test))
            logger.info("Numeric features: %s", numeric_cols)
            logger.info("Categorical features: %s", categorical_cols)
        pbar.update(1)

        # computing the upper bound for clipping 'trip_distance' based on training data
        clip_upper = None
        if "trip_distance" in X_train.columns:
            clip_upper = float(np.nanpercentile(X_train["trip_distance"], 99.5))
            X_train["trip_distance"] = X_train["trip_distance"].clip(lower=0, upper=clip_upper)
            X_test["trip_distance"]  = X_test["trip_distance"].clip(lower=0, upper=clip_upper)
            logger.info("Clipped 'trip_distance' to upper bound: %.2f", clip_upper)
        pbar.update(1)
            

        with _log_step(logger, "Fit model"):
            pipe = build_pipeline(numeric_cols, categorical_cols)
            pipe.fit(X_train, y_train)
        pbar.update(1)

        with _log_step(logger, "Evaluate"):
            preds = pipe.predict(X_test)
            rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
            logger.info("RMSE = %.4f", rmse)
        pbar.update(1)

        with _log_step(logger, "Save artifacts"):
            paths = get_paths()
            dump(pipe, paths.model_path)

            metrics = {
                "rmse": rmse,
                "n_train": int(len(X_train)),
                "n_test": int(len(X_test)),
            }
            paths.metrics_path.write_text(
                json.dumps(metrics, indent=2),
                encoding="utf-8",
            )

            schema_out = {
                "target": target,
                "numeric_features": numeric_cols,
                "categorical_features": categorical_cols,
                "all_features": keep_cols,
                # upper threshold used for clipping 'trip_distance' 
                "trip_distance_clip_upper": clip_upper,
            }
            paths.schema_path.write_text(
                json.dumps(schema_out, indent=2),
                encoding="utf-8",
            )

            logger.info("Saved model to: %s", paths.model_path)
            logger.info("Saved metrics to: %s", paths.metrics_path)
            logger.info("Saved schema to: %s", paths.schema_path)
        pbar.update(1)


if __name__ == "__main__":
    main()
