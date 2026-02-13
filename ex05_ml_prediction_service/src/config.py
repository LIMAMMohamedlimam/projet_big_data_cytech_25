"""
Configuration module.

This file centralizes environment variable access for MinIO/S3 and
artifact paths.

NumpyDoc style docstrings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class S3Config:
    """S3/MinIO configuration.

    Attributes
    ----------
    endpoint_url : str
        S3 endpoint URL (e.g. "http://localhost:9000").
    access_key : str
        Access key for MinIO/S3.
    secret_key : str
        Secret key for MinIO/S3.
    region : str
        Region name (often "us-east-1" for MinIO).
    """

    endpoint_url: str
    access_key: str
    secret_key: str
    region: str = "us-east-1"


@dataclass(frozen=True)
class Paths:
    """Project paths.

    Attributes
    ----------
    artifacts_dir : Path
        Directory where artifacts are saved.
    model_path : Path
        Path to the serialized model pipeline.
    metrics_path : Path
        Path to metrics json.
    schema_path : Path
        Path to schema json.
    """

    artifacts_dir: Path
    model_path: Path
    metrics_path: Path
    schema_path: Path


def get_s3_config() -> S3Config:
    """Load S3 configuration from environment variables.

    Expected environment variables
    ------------------------------
    MINIO_ENDPOINT_URL
    MINIO_ACCESS_KEY
    MINIO_SECRET_KEY
    MINIO_REGION (optional)

    Returns
    -------
    S3Config
        Loaded configuration.

    Raises
    ------
    RuntimeError
        If required variables are missing.
    """
    endpoint = os.getenv("MINIO_ENDPOINT_URL", "").strip()
    access = os.getenv("MINIO_ACCESS_KEY", "").strip()
    secret = os.getenv("MINIO_SECRET_KEY", "").strip()
    region = os.getenv("MINIO_REGION", "us-east-1").strip()

    missing = [k for k, v in {
        "MINIO_ENDPOINT_URL": endpoint,
        "MINIO_ACCESS_KEY": access,
        "MINIO_SECRET_KEY": secret,
    }.items() if not v]

    if missing:
        raise RuntimeError(
            f"Missing env vars: {', '.join(missing)}. "
            "Export MinIO credentials before running."
        )

    return S3Config(endpoint_url=endpoint, access_key=access, secret_key=secret, region=region)


def get_paths() -> Paths:
    """Get artifact paths.

    Returns
    -------
    Paths
        Paths for saving outputs.
    """
    artifacts_dir = Path(__file__).resolve().parents[1] / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    return Paths(
        artifacts_dir=artifacts_dir,
        model_path=artifacts_dir / "model.joblib",
        metrics_path=artifacts_dir / "metrics.json",
        schema_path=artifacts_dir / "schema.json",
    )