#!/usr/bin/env python3
"""
Multipart uploader for large files — Jupyter Notebook Edition.
All argparse CLI code is removed and replaced with variables.
"""

import logging
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import boto3
from botocore.config import Config
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    ReadTimeoutError,
    ConnectTimeoutError,
)

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("MultipartUploader")

# -----------------------------------------------------------------------------
# LargeMultipartUploader Class
# -----------------------------------------------------------------------------
class LargeMultipartUploader:
    """Upload a large file using robust multipart uploads."""

    def __init__(
        self,
        *,
        file_path: str,
        bucket: str,
        key: str,
        region: str,
        access_key: str,
        secret_key: str,
        endpoint: str,
        part_size: int = 50 * 1024 * 1024,
        max_retries: int = 5,
    ) -> None:
        self.file_path = file_path
        self.bucket = bucket
        self.key = key
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint = endpoint
        self.part_size = part_size
        self.max_retries = max_retries

        self.progress_lock = Lock()
        self.parts_completed = 0

        self.session = boto3.session.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
        )
        self.botocore_cfg = Config(
            region_name=self.region,
            retries={"max_attempts": self.max_retries, "mode": "standard"},
        )
        self.s3 = self.session.client(
            "s3", config=self.botocore_cfg, endpoint_url=self.endpoint
        )
        self.upload_id: str | None = None

    # Helper Methods ----------------------------------------------------
    @staticmethod
    def human_mb_per_s(num_bytes: int, seconds: float) -> float:
        return (num_bytes / (1024 * 1024)) / seconds if seconds > 0 else float("inf")

    @staticmethod
    def is_insufficient_storage_error(exc: Exception) -> bool:
        if isinstance(exc, ClientError):
            meta = exc.response.get("ResponseMetadata", {})
            return meta.get("HTTPStatusCode") == 507
        return False

    @staticmethod
    def is_524_error(exc: Exception) -> bool:
        if isinstance(exc, ClientError):
            meta = exc.response.get("ResponseMetadata", {})
            return meta.get("HTTPStatusCode") == 524
        return False

    @staticmethod
    def is_no_such_upload_error(exc: Exception) -> bool:
        if isinstance(exc, ClientError):
            err = exc.response.get("Error", {})
            return err.get("Code") == "NoSuchUpload"
        return False

    def call_with_524_retry(self, description: str, func):
        for attempt in range(1, self.max_retries + 1):
            try:
                return func()
            except ClientError as exc:
                if self.is_524_error(exc):
                    logger.warning(
                        f"{description}: received 524 response (attempt {attempt})"
                    )
                    if attempt == self.max_retries:
                        logger.error(f"{description}: exceeded max_retries for 524")
                        raise
                    backoff = 2**attempt
                    logger.info(f"{description}: retrying in {backoff}s...")
                    time.sleep(backoff)
                    continue
                raise
            except (ReadTimeoutError, ConnectTimeoutError) as exc:
                logger.warning(
                    f"{description}: request timed out (attempt {attempt}): {exc}"
                )
                if attempt == self.max_retries:
                    logger.error(f"{description}: exceeded max_retries for timeout")
                    raise
                backoff = 2**attempt
                logger.info(f"{description}: retrying in {backoff}s...")
                time.sleep(backoff)

    # ------------------------------------------------------------------
    # Multi-part Completion with Timeout Logic
    # ------------------------------------------------------------------
    def complete_with_timeout_retry(
        self,
        *,
        parts_sorted: list,
        initial_timeout: int,
        expected_size: int,
    ):
        if self.upload_id is None:
            raise RuntimeError("upload_id not set")

        timeout = initial_timeout
        cfg = self.botocore_cfg
        last_exc: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            cfg = cfg.merge(Config(read_timeout=timeout, connect_timeout=timeout))
            client = self.session.client("s3", config=cfg, endpoint_url=self.endpoint)
            try:
                client.complete_multipart_upload(
                    Bucket=self.bucket,
                    Key=self.key,
                    UploadId=self.upload_id,
                    MultipartUpload={"Parts": parts_sorted},
                )
                self.s3 = client
                self.botocore_cfg = cfg
                return
            except (ReadTimeoutError, ConnectTimeoutError) as exc:
                last_exc = exc
            except (ClientError, BotoCoreError) as exc:
                last_exc = exc

            logger.info(f"Retrying complete_multipart_upload, waiting {timeout}s")
            time.sleep(timeout)

            try:
                head = self.call_with_524_retry(
                    "head_object",
                    lambda: client.head_object(Bucket=self.bucket, Key=self.key),
                )
                if head.get("ContentLength") == expected_size:
                    logger.info("Upload merge completed successfully via HeadObject")
                    self.s3 = client
                    return
            except Exception:
                pass

            if attempt == self.max_retries:
                raise last_exc or RuntimeError("Final upload completion failed")

            timeout *= 2

    # ------------------------------------------------------------------
    # Upload a single part
    # ------------------------------------------------------------------
    def upload_part(
        self,
        *,
        part_number: int,
        offset: int,
        bytes_to_read: int,
        total_parts: int,
        start_time: float,
    ) -> dict:

        if self.upload_id is None:
            raise RuntimeError("upload_id not set")

        for attempt in range(1, self.max_retries + 1):
            try:
                with open(self.file_path, "rb") as f:
                    f.seek(offset)
                    data = f.read(bytes_to_read)

                resp = self.s3.upload_part(
                    Bucket=self.bucket,
                    Key=self.key,
                    PartNumber=part_number,
                    UploadId=self.upload_id,
                    Body=data,
                )
                etag = resp["ETag"]

                with self.progress_lock:
                    self.parts_completed += 1
                    progress = 100.0 * self.parts_completed / total_parts

                return {"PartNumber": part_number, "ETag": etag}

            except Exception as exc:
                if attempt == self.max_retries:
                    raise
                time.sleep(2**attempt)

    # ------------------------------------------------------------------
    # Main Upload Process
    # ------------------------------------------------------------------
    def upload(self) -> None:

        file_size = os.path.getsize(self.file_path)
        total_parts = math.ceil(file_size / self.part_size)

        start_time = time.time()
        file_gb = file_size / float(1024**3)
        completion_timeout = max(60, int(math.ceil(file_gb) * 5))

        resp = self.call_with_524_retry(
            "create_multipart_upload",
            lambda: self.s3.create_multipart_upload(Bucket=self.bucket, Key=self.key),
        )
        self.upload_id = resp["UploadId"]

        parts: list[dict] = []
        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {}
                for part_num in range(1, total_parts + 1):
                    offset = (part_num - 1) * self.part_size
                    chunk_size = min(self.part_size, file_size - offset)
                    futures[
                        executor.submit(
                            self.upload_part,
                            part_number=part_num,
                            offset=offset,
                            bytes_to_read=chunk_size,
                            total_parts=total_parts,
                            start_time=start_time,
                        )
                    ] = part_num

                for fut in as_completed(futures):
                    parts.append(fut.result())

            parts_sorted = sorted(parts, key=lambda x: x["PartNumber"])

            self.complete_with_timeout_retry(
                parts_sorted=parts_sorted,
                initial_timeout=completion_timeout,
                expected_size=file_size,
            )

        except Exception as exc:
            raise

        elapsed = time.time() - start_time
        speed = self.human_mb_per_s(file_size, elapsed)
        print(f"Upload complete! Speed: {speed:.2f} MB/s")

# -----------------------------------------------------------------------------
# PARAMETERS (Set these in your Notebook Cell)
# -----------------------------------------------------------------------------

bucket = "YOUR_BUCKET"
key = "dest/path/in/bucket/filename"
file_path = "/path/to/local/hugefile.bin"

region = "us-east-1"
endpoint = "https://your-s3-endpoint.example.com"

access_key = "YOUR_ACCESS_KEY"
secret_key = "YOUR_SECRET_KEY"

chunk_size = 50 * 1024 * 1024   # 50MB
max_retries = 5

# -----------------------------------------------------------------------------
# RUN IT
# -----------------------------------------------------------------------------

uploader = LargeMultipartUploader(
    file_path=file_path,
    bucket=bucket,
    key=key,
    region=region,
    access_key=access_key,
    secret_key=secret_key,
    endpoint=endpoint,
    part_size=chunk_size,
    max_retries=max_retries,
)

uploader.upload()
