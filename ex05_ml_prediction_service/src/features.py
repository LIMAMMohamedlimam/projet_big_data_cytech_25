"""
Feature engineering for NYC Yellow Taxi trips.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional


def make_features(df: pd.DataFrame , trip_distance_clip_upper: Optional[float] = None) -> pd.DataFrame:
    """Create ML features from raw taxi trip records.

    Parameters
    ----------
    df : pandas.DataFrame
        Raw input dataframe.
    trip_distance_clip_upper : Optional[float], default=None
        If set, clip the 'trip_distance' feature to this upper bound to reduce 
        the influence of outliers. If None, no clipping is applied.

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
        out["trip_duration_min"] = dur
    else:
        out["trip_duration_min"] = np.nan

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

    # clip only if a threshold is provided
    if "trip_distance" in out.columns:
        out["trip_distance"] = pd.to_numeric(out["trip_distance"], errors="coerce")
        if trip_distance_clip_upper is not None:
            out["trip_distance"] = out["trip_distance"].clip(lower=0, upper=trip_distance_clip_upper)
    return out