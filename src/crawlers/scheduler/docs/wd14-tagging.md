# WD14 Image Tagging System

Complete WD14 ONNX-based image tagging pipeline with bucket enumeration, batch processing, and Valkey/Neo4j caching.

## Overview

WD14 is a specialized image tagging model that automatically generates character and general tags with high precision. This system:

- Discovers images in random S3 buckets
- Tags with WD14 ONNX model (local 8GB CUDA GPU)
- Filters tags by 95% confidence threshold
- Caches results in Valkey (fast lookup) and Neo4j (graph relationships)
- Keeps metadata completely separate from CLIP tagging ontology

## Architecture

```
S3 Bucket (images)
    ↓
[scan] Discover images via enumeration
    ↓ (BucketPointer: {bucket, prefix, sha256, s3_uri})
Valkey Cache
    ├─ wd14:tags:{sha256} → WD14Result (TTL: 7 days)
    ├─ wd14:failed:{sha256} → error tracking
    └─ wd14:discovered:{bucket} → scan metadata
    ↓
[process] Batch WD14 inference
    ├─ Download from S3
    ├─ ONNX inference (CUDA-accelerated)
    ├─ Filter by 95% confidence
    └─ Store result
    ↓
Neo4j Graph (persistent storage)
    ├─ WD14Result nodes
    ├─ WD14Tag nodes (by category)
    └─ ImageMedia → HAS_WD14_RESULT → WD14Result
```

## Installation

WD14 dependencies are added to requirements.txt:

```
onnxruntime-gpu>=1.18.0      # CUDA-accelerated ONNX
onnx>=1.15.0                 # ONNX format support
huggingface-hub>=0.20.0      # Model download
timm>=0.9.0                  # PyTorch model utilities
```

Rebuild docker container:
```bash
docker compose build --no-cache jupyterlab
```

## Usage

### Command Line Interface

#### 1. Scan Bucket for Images

Discover images in S3 bucket and register for processing:

```bash
python -m src.feed.services.wd14_cli scan --bucket my-bucket [--prefix images/]
```

Output:
```
Found 1250 images, 450 new
Bucket: my-bucket
Prefix: images/
```

#### 2. Process Discovered Images

Tag images with WD14 model:

```bash
# Process all discovered images
python -m src.feed.services.wd14_cli process --bucket my-bucket

# Limit processing
python -m src.feed.services.wd14_cli process --bucket my-bucket --limit 100

# With custom batch size (for 8GB VRAM)
python -m src.feed.services.wd14_cli process --bucket my-bucket --batch-size 32
```

Progress output:
```
Scanning my-bucket...
Found 450 images, 450 new
Processing 450 images...
Progress: 0/450
Progress: 10/450
Results: 445 success, 5 failed
```

#### 3. Check Status

View tagging statistics:

```bash
python -m src.feed.services.wd14_cli status
```

Output:
```
WD14 Cache Status
  Cached tags: 1250
  Failed jobs: 5
```

#### 4. Get Tags for Image

Retrieve cached tags by SHA256:

```bash
python -m src.feed.services.wd14_cli tags abc123def456...
```

Output:
```
Image: abc123def456...
Rating: safe
Model: wd14-vit
Processed: 2025-01-15T10:30:00

Character Tags:
  1girl: 99.80%
  blue_eyes: 95.20%

General Tags:
  outdoor: 98.50%
  sky: 97.80%
  ... and 18 more
```

#### 5. Retry Failed Jobs

Reprocess images that failed earlier:

```bash
# Retry jobs failed > 24 hours ago
python -m src.feed.services.wd14_cli retry --older-than 24
```

### Python API

```python
from src.feed.services.wd14_service import WD14Service

service = WD14Service()

# Scan bucket
images, new_count = service.scan_bucket("my-bucket", prefix="images/")

# Process batch
stats = service.process_batch(images, limit=100)
print(f"Success: {stats['success']}, Failed: {stats['failed']}")

# Retrieve tags
result = service.get_tags("abc123def456...")
for tag in result.get_high_confidence_tags(threshold=0.95):
    print(f"{tag.name}: {tag.confidence:.1%}")

# Check statistics
stats = service.get_stats()
print(f"Cached: {stats['cached_tags']}, Failed: {stats['failed_jobs']}")
```

## Data Model

### WD14Result

Represents the tagging result for a single image:

```python
from src.image_captioning.models import WD14Result, WD14Tag, WD14TagCategory

result = WD14Result(
    image_sha256="abc123...",
    character_tags=[
        WD14Tag(name="1girl", category=WD14TagCategory.CHARACTER, confidence=0.99),
    ],
    general_tags=[
        WD14Tag(name="outdoor", category=WD14TagCategory.GENERAL, confidence=0.98),
        WD14Tag(name="sky", category=WD14TagCategory.GENERAL, confidence=0.97),
    ],
    rating="safe",  # safe, questionable, or explicit
    model_version="wd14-vit",
)

# Get high-confidence tags (95% threshold)
high_conf = result.get_high_confidence_tags(threshold=0.95)
```

### Storage

**Valkey Cache** (Fast Lookup):
- `wd14:tags:{sha256}` → JSON WD14Result (7-day TTL)
- `wd14:failed:{sha256}` → Error metadata
- `wd14:discovered:{bucket}` → Scan metadata

**Neo4j Graph** (Persistent, Separate Ontology):
```
WD14Result node:
  - image_sha256 (unique)
  - rating: safe | questionable | explicit
  - processed_at: timestamp
  - model_version: "wd14-vit"

WD14Tag node:
  - name: string
  - category: character | general | rating
  - (unique on name + category)

Relationships:
  ImageMedia -[:HAS_WD14_RESULT]-> WD14Result
  WD14Result -[:HAS_TAG {confidence}]-> WD14Tag
```

## Configuration

Edit `src/image_captioning/config.py`:

```python
@dataclass
class WD14Config:
    model_repo: str = "SmilingWolf/wd-v1-4-vit-tagger-v2"
    confidence_threshold: float = 0.95      # Filter tags
    device: str = "cuda"                     # cuda or cpu
    batch_size: int = 32                     # For 8GB VRAM
    providers: List[str] = [
        "CUDAExecutionProvider",
        "CPUExecutionProvider"
    ]
    model_cache_dir: Optional[Path] = None   # Auto: ~/.cache/wd14_models/
```

## Performance

### Hardware Requirements

- **GPU**: NVIDIA with 8GB VRAM (tested on RTX 3060)
- **Memory**: Batch size 32 = ~6-7GB VRAM
- **CPU**: 4+ cores for preprocessing/I/O

### Throughput

- ~40-50 images/minute on RTX 3060 (batch 32)
- S3 download overhead: ~1-2 sec per image
- ONNX inference: ~0.1-0.15 sec per image
- Valkey caching: <1ms per lookup

## Troubleshooting

### CUDA Out of Memory

Reduce batch size in config:
```python
config.wd14.batch_size = 16  # or 8
```

### Slow Processing

Check S3 connection and bandwidth:
```bash
python -m src.feed.services.wd14_cli status
# Monitor network throughput during processing
```

### Failed Tags Not Retrying

Manually retry:
```bash
python -m src.feed.services.wd14_cli retry --older-than 1
```

## Separate Ontology

WD14 tags are kept completely separate from CLIP tags:

- **WD14**: Character + General categories, SmilingWolf/wd-v1-4-vit model
- **CLIP**: Semantic embeddings via openai/clip-vit-base-patch32

Both systems can tag the same image without interference:

```python
# WD14 tags (this system)
wd14_result = service.get_tags(sha256)

# CLIP tags (separate system)
from src.image_captioning.auto_tagger import CLIPAutoTagger
clip_tags = CLIPAutoTagger().tag_image(image)
```

## Future Enhancements

- [ ] Support for additional WD14 model variants
- [ ] Character classification refinement (anime-specific)
- [ ] Integration with reverse image search pipeline
- [ ] Distributed processing (RunPod serverless)
