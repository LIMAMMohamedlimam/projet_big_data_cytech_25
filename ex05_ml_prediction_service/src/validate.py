"""
Validation utilities for training and inference inputs.

We validate schema presence + basic constraints based on the data dictionary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

import pandas as pd


@dataclass(frozen=True)
class Schema:
    """Expected schema definition.

    Attributes
    ----------
    required_features : list of str
        Columns required for inference.
    target : str
        Target column name used for training.
    optional_features : list of str
        Optional columns accepted if present.
    """

    required_features: List[str]
    target: str
    optional_features: List[str]


DEFAULT_SCHEMA = Schema(
    required_features=[
        "tpep_pickup_datetime",
        "trip_distance",
        "PULocationID",
        "DOLocationID",
    ],
    target="total_amount",
    optional_features=[
        "tpep_dropoff_datetime",
        "passenger_count",
        "VendorID",
        "RatecodeID",
        "store_and_fwd_flag",
        "payment_type",
    ],
)


def _missing_cols(df: pd.DataFrame, cols: Iterable[str]) -> List[str]:
    """Return missing columns from df."""
    return [c for c in cols if c not in df.columns]


def validate_inference_frame(df: pd.DataFrame, schema: Schema = DEFAULT_SCHEMA) -> None:
    """Validate input dataframe for inference.

    Parameters
    ----------
    df : pandas.DataFrame
        Input data for prediction.
    schema : Schema, default=DEFAULT_SCHEMA
        Schema definition.

    Raises
    ------
    ValueError
        If required columns are missing or constraints are violated.
    """
    missing = _missing_cols(df, schema.required_features)
    if missing:
        raise ValueError(f"Missing required columns for inference: {missing}")

    # basic type/date parsing checks (do not mutate, only check)
    _validate_constraints(df)


def validate_training_frame(df: pd.DataFrame, schema: Schema = DEFAULT_SCHEMA) -> None:
    """Validate input dataframe for training.

    Parameters
    ----------
    df : pandas.DataFrame
        Training dataset including target.
    schema : Schema, default=DEFAULT_SCHEMA
        Schema definition.

    Raises
    ------
    ValueError
        If required columns or target are missing or constraints violated.
    """
    missing = _missing_cols(df, schema.required_features + [schema.target])
    if missing:
        raise ValueError(f"Missing required columns for training: {missing}")

    _validate_constraints(df, target=schema.target)


def _validate_constraints(df: pd.DataFrame, target: Optional[str] = None) -> None:
    """Validate core constraints and domain checks.

    Parameters
    ----------
    df : pandas.DataFrame
        Input data.
    target : str, optional
        Target column name. If provided, validates it too.

    Raises
    ------
    ValueError
        If constraints are violated.
    """
    # Non-negative checks
    if (df["trip_distance"] < 0).any():
        raise ValueError("trip_distance contains negative values.")

    if "passenger_count" in df.columns:
        if (df["passenger_count"] < 0).any():
            raise ValueError("passenger_count contains negative values.")

    # Datetime ordering if dropoff is present
    if "tpep_dropoff_datetime" in df.columns:
        pickup = pd.to_datetime(df["tpep_pickup_datetime"], errors="coerce")
        dropoff = pd.to_datetime(df["tpep_dropoff_datetime"], errors="coerce")
        if pickup.isna().any():
            raise ValueError("tpep_pickup_datetime contains unparsable values.")
        if dropoff.isna().any():
            raise ValueError("tpep_dropoff_datetime contains unparsable values.")
        if (dropoff < pickup).any():
            raise ValueError("Some rows have dropoff earlier than pickup.")

    # VendorID allowed values (as per dictionary)
    if "VendorID" in df.columns:
        allowed_vendor = {1, 2, 6, 7}
        bad = df.loc[~df["VendorID"].isin(allowed_vendor) & df["VendorID"].notna(), "VendorID"]
        if not bad.empty:
            raise ValueError(f"VendorID has invalid values: {sorted(bad.unique().tolist())}")

    # RatecodeID common allowed values
    if "RatecodeID" in df.columns:
        allowed_rate = {1, 2, 3, 4, 5, 6, 99}
        bad = df.loc[~df["RatecodeID"].isin(allowed_rate) & df["RatecodeID"].notna(), "RatecodeID"]
        if not bad.empty:
            raise ValueError(f"RatecodeID has invalid values: {sorted(bad.unique().tolist())}")

    # store_and_fwd_flag should be Y/N if present
    if "store_and_fwd_flag" in df.columns:
        allowed_flag = {"Y", "N"}
        bad = df.loc[~df["store_and_fwd_flag"].isin(allowed_flag) & df["store_and_fwd_flag"].notna(),
                     "store_and_fwd_flag"]
        if not bad.empty:
            raise ValueError(f"store_and_fwd_flag has invalid values: {sorted(bad.unique().tolist())}")

    # payment_type typical allowed values 0..6
    if "payment_type" in df.columns:
        bad = df.loc[~df["payment_type"].between(0, 6) & df["payment_type"].notna(), "payment_type"]
        if not bad.empty:
            raise ValueError(f"payment_type has invalid values: {sorted(bad.unique().tolist())}")

    if target is not None:
        if (df[target] < 0).any():
            # total_amount can be negative in rare refund/adjustment cases,
            # but we keep it strict unless you want to allow it.
            raise ValueError(f"{target} contains negative values.")