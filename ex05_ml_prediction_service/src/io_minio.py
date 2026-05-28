"""
I/O for reading parquet data from MinIO/S3 or local filesystem.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from .config import S3Config


def read_parquet_any(path: str, s3: Optional[S3Config] = None) -> pd.DataFrame:
    """Read a parquet file either locally or from S3/MinIO.

    Parameters
    ----------
    path : str
        Local path or S3 URI (e.g. "s3://bucket/key.parquet").
    s3 : S3Config, optional
        S3 connection info. Required if `path` is an S3 URI.

    Returns
    -------
    pandas.DataFrame
        Loaded dataset.

    Raises
    ------
    ValueError
        If path is S3 but S3 config is missing.
    """
    if path.startswith("s3://"):
        if s3 is None:
            raise ValueError("S3 path provided but S3Config is None.")

        endpoint = s3.endpoint_url.rstrip("/")

        storage_options = {
            # Credentials
            "key": s3.access_key,
            "secret": s3.secret_key,

            # Important: MinIO endpoint
            "client_kwargs": {
                "endpoint_url": endpoint,
                "region_name": s3.region,
            },

            # CRITICAL: force path-style (MinIO often needs it)
            "config_kwargs": {
                "s3": {"addressing_style": "path"}
            },

            # If your endpoint is http://..., keep ssl False
            "use_ssl": endpoint.startswith("https://"),
        }

        return pd.read_parquet(path, storage_options=storage_options)

    return pd.read_parquet(path)




if __name__ == "__main__":
    import s3fs
    from src.config import get_s3_config
    s3 = get_s3_config()
    fs = s3fs.S3FileSystem(
        key=s3.access_key,
        secret=s3.secret_key,
        client_kwargs={"endpoint_url": s3.endpoint_url, "region_name": s3.region},
        config_kwargs={"s3": {"addressing_style": "path"}},
        use_ssl=s3.endpoint_url.startswith("https://"),
    )

    print("Endpoint:", s3.endpoint_url)
    print("Buckets:", fs.ls("s3://"))
    print("Objects in bucket:", fs.ls("s3://nyc-cleaned/")[:20])