"""Unit tests for inference-time input validation.

This module checks that `validate_inference_frame` accepts valid inference
frames and raises errors when required columns are missing.
"""
import pandas as pd
import pytest

from src.validate import validate_inference_frame


def test_validate_inference_ok() -> None:
    """Validate that a minimal valid inference dataframe passes.

    Notes
    -----
    The input dataframe includes the required columns:
    `tpep_pickup_datetime`, `trip_distance`, `PULocationID`, `DOLocationID`. [web:1]
    """
    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": ["2025-01-01 10:00:00"],
            "trip_distance": [3.0],
            "PULocationID": [10],
            "DOLocationID": [20],
        }
    )
    validate_inference_frame(df)


def test_validate_inference_missing_required() -> None:
    """Validate that missing required columns raise an error.

    Raises
    ------
    ValueError
        Expected when one or more required columns are missing. [web:4]
    """
    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": ["2025-01-01 10:00:00"],
            "trip_distance": [3.0],
            "PULocationID": [10],
            # Missing DOLocationID
        }
    )
    with pytest.raises(ValueError):
        validate_inference_frame(df)
