"""Shared S3 client factory for SeaweedFS (and S3-compatible stores)."""

import gzip
import json
import logging
import os
from io import BytesIO
from typing import Optional

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.client import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

_MULTIPART_THRESHOLD = 50 * 1024 * 1024  # 50 MB


class S3Store:
    """S3-compatible object store client backed by boto3.

    Configuration via environment variables:
        S3_ENDPOINT     — full URL, e.g. http://localhost:8333
        S3_ACCESS_KEY   — access key
        S3_SECRET_KEY   — secret key
        S3_BUCKET       — default bucket (overridable per-call)
    """

    def __init__(self, bucket: str = "raw-data"):
        endpoint = os.environ.get("S3_ENDPOINT", "http://localhost:8333")
        access_key = os.environ.get("S3_ACCESS_KEY", "admin")
        secret_key = os.environ.get("S3_SECRET_KEY", "password")
        self.bucket = os.environ.get("S3_BUCKET", bucket)

        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        self._transfer_config = TransferConfig(
            multipart_threshold=_MULTIPART_THRESHOLD,
            multipart_chunksize=_MULTIPART_THRESHOLD,
        )

    def save_raw(self, data: dict, path: str) -> str:
        """Gzip-compress a dict and upload to S3.

        Args:
            data: JSON-serialisable dict.
            path: Object key (`.gz` appended if not present).

        Returns:
            The final object key.
        """
        if not path.endswith(".gz"):
            path += ".gz"

        buf = BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
            gz.write(json.dumps(data).encode())
        buf.seek(0)

        self._client.put_object(
            Bucket=self.bucket,
            Key=path,
            Body=buf,
            ContentType="application/json",
            ContentEncoding="gzip",
        )
        logger.debug("saved raw data to s3://%s/%s", self.bucket, path)
        return path

    def upload_file(self, local_path: str, key: str, bucket: Optional[str] = None) -> str:
        """Upload a local file to S3.

        Uses multipart upload for files larger than 50 MB.

        Args:
            local_path: Absolute path on disk.
            key: Destination object key.
            bucket: Override the default bucket.

        Returns:
            The object key.
        """
        target_bucket = bucket or self.bucket
        self._client.upload_file(
            local_path,
            target_bucket,
            key,
            Config=self._transfer_config,
        )
        logger.debug("uploaded %s to s3://%s/%s", local_path, target_bucket, key)
        return key

    def download_file(self, key: str, local_path: str, bucket: Optional[str] = None) -> bool:
        """Download an object to a local path.

        Returns:
            True on success, False if the object does not exist.
        """
        target_bucket = bucket or self.bucket
        try:
            self._client.download_file(target_bucket, key, local_path)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise

    def object_exists(self, key: str, bucket: Optional[str] = None) -> bool:
        """Return True if the object exists in S3."""
        target_bucket = bucket or self.bucket
        try:
            self._client.head_object(Bucket=target_bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise

    def generate_presigned_url(
        self, key: str, expires: int = 86400, bucket: Optional[str] = None
    ) -> str:
        """Generate a presigned GET URL for an object.

        Args:
            key: Object key.
            expires: TTL in seconds (default 24 h).
            bucket: Override the default bucket.

        Returns:
            Presigned URL string.
        """
        target_bucket = bucket or self.bucket
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": target_bucket, "Key": key},
            ExpiresIn=expires,
        )
