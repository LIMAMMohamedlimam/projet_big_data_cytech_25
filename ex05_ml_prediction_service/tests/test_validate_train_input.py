"""Unit tests for training-time input validation.

This module verifies that `validate_training_frame` accepts a minimal valid
training dataframe, and raises `ValueError` when the target is missing or when
numerical constraints are violated (e.g., negative distance).
"""
import pandas as pd
import pytest

from src.validate import validate_training_frame


def test_validate_training_ok() -> None:
    """Validate that a minimal valid training dataframe passes.

    Notes
    -----
    The input dataframe includes required columns for training, including the
    target column `total_amount`. [web:1]
    """
    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": ["2025-01-01 10:00:00"],
            "trip_distance": [2.5],
            "PULocationID": [100],
            "DOLocationID": [200],
            "total_amount": [15.0],
        }
    )
    validate_training_frame(df)


def test_validate_training_missing_target() -> None:
    """Validate that missing target column raises an error.

    Raises
    ------
    ValueError
        Expected when the target column required for training is missing. [web:4]
    """
    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": ["2025-01-01 10:00:00"],
            "trip_distance": [2.5],
            "PULocationID": [100],
            "DOLocationID": [200],
        }
    )
    with pytest.raises(ValueError):
        validate_training_frame(df)


def test_validate_training_negative_distance() -> None:
    """Validate that negative trip distances raise an error.

    Raises
    ------
    ValueError
        Expected when `trip_distance` is negative. [web:4]
    """
    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": ["2025-01-01 10:00:00"],
            "trip_distance": [-1.0],
            "PULocationID": [100],
            "DOLocationID": [200],
            "total_amount": [10.0],
        }
    )
    with pytest.raises(ValueError):
        validate_training_frame(df)
