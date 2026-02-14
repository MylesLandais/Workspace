# MinIO Storage Guide

This guide explains how to use the local MinIO S3-compatible storage for cached images, mock data, and temporary files.

## Overview

The project uses MinIO (S3-compatible object storage) for:
- **mock-data bucket**: Test/mock data images
- **cache bucket**: Cached images and generated content
- **temp bucket**: Temporary files
- **media bucket**: Production media files

## Setup

### 1. Start MinIO Service

MinIO is already configured in the media-platform docker-compose. Start it:

```bash
cd media-platform
docker compose up -d minio
```

Or use the full setup script:

```bash
cd media-platform
npm run setup
```

### 2. Create Standard Buckets

Run in Docker container:

```bash
# If using Docker container
docker exec -it jupyterlab python /home/jovyan/workspaces/scripts/setup_minio_buckets.py

# Or if running locally with Python
python scripts/setup_minio_buckets.py
```

This creates:
- `mock-data` - For mock/test data images
- `cache` - For cached images
- `temp` - For temporary files
- `media` - For production media

### 3. Access MinIO Console

- **URL**: http://localhost:9001
- **Username**: `minioadmin`
- **Password**: `minioadmin`

## Usage

### Python API

#### Image Cache

```python
from src.storage.s3_cache import get_image_cache

# Get cache instance
cache = get_image_cache(bucket_name="cache")

# Store image
image_bytes = b"..."
key = cache.store_image(image_bytes, key="my-image.jpg")

# Check if exists
if cache.image_exists("my-image.jpg"):
    # Get presigned URL
    url = cache.get_image_url("my-image.jpg", expires_seconds=3600)
    print(f"Image URL: {url}")

# Download to local file
cache.download_image("my-image.jpg", "/tmp/local-image.jpg")
```

#### Temporary File Storage

```python
from src.storage.s3_cache import get_temp_storage

# Get temp storage instance
temp = get_temp_storage(bucket_name="temp")

# Store file from bytes
file_data = b"..."
key = temp.store_file(file_data, "data.json", subdir="2025-01-01")

# Store file from local path
key = temp.store_file_from_path(
    "/path/to/file.jpg",
    filename="uploaded.jpg",
    subdir="uploads"
)

# Get presigned URL
url = temp.get_file_url("data.json", subdir="2025-01-01")

# Download to local
temp.download_file("data.json", "/tmp/data.json", subdir="2025-01-01")
```

#### Direct MinIO Connection

```python
from src.feed.storage.minio_connection import get_minio_connection

minio = get_minio_connection()

# Ensure bucket exists
minio.ensure_bucket("my-bucket")

# Upload file
minio.upload_file("my-bucket", "path/to/file.jpg", "/local/file.jpg")

# Upload bytes
minio.upload_bytes("my-bucket", "path/to/data.json", b'{"key": "value"}')

# Check if exists
if minio.object_exists("my-bucket", "path/to/file.jpg"):
    print("File exists!")

# Generate presigned URL
url = minio.generate_presigned_url(
    "my-bucket",
    "path/to/file.jpg",
    expires_seconds=3600
)

# Download file
minio.download_file("my-bucket", "path/to/file.jpg", "/local/file.jpg")
```

## Migration Scripts

### Migrate Mock Data to MinIO

Migrate all images from `mock_data/` directory to MinIO:

```bash
# In Docker container
docker exec -it jupyterlab python /home/jovyan/workspaces/scripts/migrate_mock_data_to_minio.py --dry-run

# Actually migrate
docker exec -it jupyterlab python /home/jovyan/workspaces/scripts/migrate_mock_data_to_minio.py

# Or locally
python scripts/migrate_mock_data_to_minio.py --dry-run
python scripts/migrate_mock_data_to_minio.py
```

## Environment Configuration

MinIO connection is configured via environment variables:

```bash
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_REGION=us-east-1
MINIO_SECURE=false
```

For production/staging, update these to point to Cloudflare R2 or GCS:

```bash
# Cloudflare R2
MINIO_ENDPOINT=https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com
MINIO_ACCESS_KEY=your_r2_access_key
MINIO_SECRET_KEY=your_r2_secret_key
MINIO_REGION=auto
MINIO_SECURE=true

# Google Cloud Storage (via S3 API)
MINIO_ENDPOINT=https://storage.googleapis.com
MINIO_ACCESS_KEY=your_gcp_access_key
MINIO_SECRET_KEY=your_gcp_secret_key
MINIO_REGION=us-central1
MINIO_SECURE=true
```

## Bucket Organization

### Recommended Structure

```
mock-data/
  images/
    AddisonRae/
      image1.jpg
      image2.jpg
    ...
    
cache/
  images/
    sha256-hash.jpg
    generated/
      workflow-123/
        output.png
        
temp/
  files/
    uploads/
      2025-01-01/
        file1.jpg
    processing/
      task-123/
        intermediate.json
        
media/
  production/
    user-uploads/
    processed/
```

## Best Practices

1. **Use presigned URLs** for temporary access instead of making objects public
2. **Organize by date/subdirectory** for easier management
3. **Use content-type headers** for proper MIME type handling
4. **Check if object exists** before uploading to avoid duplicates
5. **Use hash-based keys** for cache objects to enable deduplication

## Integration Examples

### Replace Local File Storage

**Before:**
```python
# Save to local filesystem
with open("/tmp/cache/image.jpg", "wb") as f:
    f.write(image_bytes)
```

**After:**
```python
# Save to MinIO
from src.storage.s3_cache import get_image_cache

cache = get_image_cache()
key = cache.store_image(image_bytes, key="image.jpg")
url = cache.get_image_url(key)
```

### Store Generated Images

```python
from src.storage.s3_cache import get_image_cache
from PIL import Image
import io

# Generate image
img = Image.new('RGB', (800, 600), color='red')
buffer = io.BytesIO()
img.save(buffer, format='JPEG')
image_bytes = buffer.getvalue()

# Store in cache
cache = get_image_cache()
key = cache.store_image(image_bytes, content_type="image/jpeg")

# Get URL for sharing
url = cache.get_image_url(key, expires_seconds=86400)  # 24 hours
print(f"Image available at: {url}")
```

## Troubleshooting

### Connection Issues

```bash
# Check if MinIO is running
docker compose ps minio

# Check MinIO logs
docker compose logs minio

# Test connection
python -c "from src.feed.storage.minio_connection import get_minio_connection; m = get_minio_connection(); print(f'Connected to {m.endpoint}')"
```

### Bucket Not Found

```bash
# List buckets
python -c "from src.feed.storage.minio_connection import get_minio_connection; m = get_minio_connection(); print([b.name for b in m.get_minio_client().list_buckets()])"

# Create bucket
python scripts/setup_minio_buckets.py
```

## Related Documentation

- [Infrastructure Decisions](../docs/INFRASTRUCTURE_DECISIONS.md) - Storage provider decisions
- [Architecture Overview](../docs/ARCHITECTURE_OVERVIEW.md) - Complete stack architecture

