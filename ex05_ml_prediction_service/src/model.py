from __future__ import annotations
from typing import List

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def build_pipeline(numeric_features: List[str], categorical_features: List[str]) -> Pipeline:
    """Build a training pipeline.

    Parameters
    ----------
    numeric_features : list of str
        Names of numeric columns.
    categorical_features : list of str
        Names of categorical columns.

    Returns
    -------
    sklearn.pipeline.Pipeline
        Full preprocessing + regressor pipeline.
    """

    numeric_pipe = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
    ])

    categorical_pipe = Pipeline(steps=[
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    preproc = ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_features),
            ("cat", categorical_pipe, categorical_features),
        ],
        remainder="drop",
    )

    reg = HistGradientBoostingRegressor(
        loss="squared_error",
        max_depth=8,
        learning_rate=0.08,
        max_iter=300,
        random_state=42,
    )

    return Pipeline(steps=[
        ("preprocess", preproc),
        ("regressor", reg),
    ])