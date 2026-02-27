# ADR-005: boto3 is preferred over the minio Python client for new code

## Status

Accepted

## Context

Two S3 client libraries are in use: the `minio` Python SDK (used in `MinioStore`) and
`boto3` (used in `S3Store`). Both work against SeaweedFS's S3-compatible API.

The minio SDK is lighter but lacks built-in multipart transfer management and presigned
URL support that matches the semantics needed for large media files. boto3 provides
`TransferConfig` with automatic multipart for files above a configurable threshold and
first-class presigned URL generation.

## Decision

New code uses `boto3` via `lib/storage/s3.py`. The existing `MinioStore` in
`src/crawlers/storage/minio_store.py` is retained for backwards compatibility but
receives no new features.

`S3Store` uses `TransferConfig(multipart_threshold=50MB)` so video uploads automatically
use multipart without caller involvement.

rclone is available as an optional tool for one-time bulk migration (MinIO → SeaweedFS)
but is not a runtime dependency.

## Consequences

- `boto3` and `botocore` added to `pyproject.toml` dependencies.
- `filelock` added for yt-dlp state file locking in the archiver.
- `MinioStore` constructor parameters are now optional (read from env vars) so it can be
  used without passing credentials explicitly.
