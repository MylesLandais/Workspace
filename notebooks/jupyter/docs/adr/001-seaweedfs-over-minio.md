# ADR-001: SeaweedFS replaces MinIO for object storage

## Status

Accepted

## Context

The system originally used MinIO as its S3-compatible object store. As the stack
converges from five services to two (SeaweedFS + PostgreSQL), we need a single blob
store that handles both general crawl data and large media archives (4K/8K video up
to 2 GB per file).

MinIO was adequate for JSON payloads but required a separate configuration path and
introduced a redundant service alongside the Postgres-backed graph store.

## Decision

Replace MinIO with SeaweedFS in single-node mode using the `server` command with
`-s3 -filer` flags. SeaweedFS exposes an S3-compatible API on port 8333, which means
all existing boto3 and minio-client code works unchanged with an endpoint swap.

Key flags:
- `-volume.max=0` — removes per-volume file count limits that silently cap large archives
- `-volume.fileSizeLimitMB=2048` — allows files up to 2 GB (covers most 4K/8K video)
- Filer metadata backend: Postgres (reuses the same DB instance, no extra service)

## Consequences

- One fewer service to operate (MinIO removed).
- Filer metadata lives in Postgres alongside feed/graph data — single backup target.
- `S3_ENDPOINT` env var replaces `MINIO_ENDPOINT`; old var retained as fallback in
  `MinioStore` for backwards compatibility.
- SeaweedFS filer UI (port 8888) provides a browsable view of stored objects.
