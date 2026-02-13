"""
Feature engineering for NYC Yellow Taxi trips.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create ML features from raw taxi trip records.

    Parameters
    ----------
    df : pandas.DataFrame
        Raw input dataframe.

    Returns
    -------
    pandas.DataFrame
        Dataframe with engineered features (does not drop original columns,
        but adds new ones).
    """
    out = df.copy()

    pickup = pd.to_datetime(out["tpep_pickup_datetime"], errors="coerce")
    out["pickup_hour"] = pickup.dt.hour.astype("Int64")
    out["pickup_dayofweek"] = pickup.dt.dayofweek.astype("Int64")
    out["pickup_month"] = pickup.dt.month.astype("Int64")

    if "tpep_dropoff_datetime" in out.columns:
        dropoff = pd.to_datetime(out["tpep_dropoff_datetime"], errors="coerce")
        dur = (dropoff - pickup).dt.total_seconds() / 60.0
        # Keep negative/NaN as is; validation should catch negative durations if dropoff exists
        out["trip_duration_min"] = dur

    # Some columns might be float but should be treated as categorical codes
    cat_like = ["VendorID", "RatecodeID", "PULocationID", "DOLocationID", "payment_type"]
    for c in cat_like:
        if c in out.columns:
            # Keep NaN; convert to Int64 if possible, else leave
            try:
                out[c] = pd.to_numeric(out[c], errors="coerce").astype("Int64")
            except TypeError:
                # If column is non-numeric, keep as is
                pass

    if "store_and_fwd_flag" in out.columns:
        out["store_and_fwd_flag"] = out["store_and_fwd_flag"].astype("object")

    # Optional: clip extreme trip_distance to reduce outlier influence
    if "trip_distance" in out.columns:
        out["trip_distance"] = pd.to_numeric(out["trip_distance"], errors="coerce")
        out["trip_distance"] = out["trip_distance"].clip(lower=0, upper=np.nanpercentile(out["trip_distance"], 99.5))

    return out