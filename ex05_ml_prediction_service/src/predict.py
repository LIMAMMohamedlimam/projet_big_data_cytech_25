"""
Inference script.

Reads an input file (CSV/JSON/JSONL) containing raw columns,
validates, applies feature engineering, loads model artifact,
and outputs predictions.

Usage
-----
python -m src.predict --input sample.csv --output pred.csv
python -m src.predict --input sample.jsonl --output pred.jsonl

Notes
-----
Input must include at least required columns:
tpep_pickup_datetime, trip_distance, PULocationID, DOLocationID.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from joblib import load

from .config import get_paths
from .features import make_features
from .validate import DEFAULT_SCHEMA, validate_inference_frame


def _read_input(path: str) -> pd.DataFrame:
    """Read an input dataset from disk.

    The reader is selected based on the file extension.

    Parameters
    ----------
    path : str
        Path to the input file. Supported extensions are ".csv", ".json",
        ".jsonl" and ".ndjson".

    Returns
    -------
    pandas.DataFrame
        Loaded input data.

    Raises
    ------
    ValueError
        If the file extension is not supported.
    """
    p = Path(path)
    ext = p.suffix.lower()

    if ext == ".csv":
        return pd.read_csv(p)
    if ext == ".json":
        return pd.read_json(p)
    if ext in {".jsonl", ".ndjson"}:
        return pd.read_json(p, lines=True)

    raise ValueError(f"Unsupported input extension: {ext}. Use CSV/JSON/JSONL.")


def _write_output(df: pd.DataFrame, path: str) -> None:
    """Write a dataset to disk.

    The writer is selected based on the file extension.

    Parameters
    ----------
    df : pandas.DataFrame
        Data to write.
    path : str
        Path to the output file. Supported extensions are ".csv", ".json",
        ".jsonl" and ".ndjson".

    Raises
    ------
    ValueError
        If the file extension is not supported.
    """
    p = Path(path)
    ext = p.suffix.lower()

    if ext == ".csv":
        df.to_csv(p, index=False)
        return
    if ext == ".json":
        df.to_json(p, orient="records", indent=2)
        return
    if ext in {".jsonl", ".ndjson"}:
        df.to_json(p, orient="records", lines=True)
        return

    raise ValueError(f"Unsupported output extension: {ext}. Use CSV/JSON/JSONL.")


def main() -> None:
    """Run batch inference from an input file and save predictions.

    This function:
    1) Parses CLI arguments,
    2) Loads the trained model artifact,
    3) Loads the feature schema (list of expected feature columns),
    4) Reads and validates raw input rows,
    5) Builds features and runs model prediction,
    6) Writes the original rows augmented with `pred_total_amount`.

    Notes
    -----
    The schema is expected to contain the key `"all_features"` that lists the
    feature column names used for inference. [web:2]

    Raises
    ------
    FileNotFoundError
        If the model or schema files pointed by the project paths do not exist.
    KeyError
        If `"all_features"` is missing from the schema.
    ValueError
        If input/output extensions are unsupported (propagated).
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input file (csv/json/jsonl)")
    parser.add_argument("--output", required=True, help="Output file (csv/json/jsonl)")
    args = parser.parse_args()

    paths = get_paths()
    model = load(paths.model_path)

    schema = json.loads(paths.schema_path.read_text(encoding="utf-8"))
    feature_cols = schema["all_features"]

    df = _read_input(args.input)
    validate_inference_frame(df, schema=DEFAULT_SCHEMA)

    df_feat = make_features(df)
    X = df_feat[feature_cols].copy()

    preds = model.predict(X)
    out = df.copy()
    out["pred_total_amount"] = preds

    _write_output(out, args.output)
    print(f"Wrote predictions to: {args.output}")


if __name__ == "__main__":
    main()
