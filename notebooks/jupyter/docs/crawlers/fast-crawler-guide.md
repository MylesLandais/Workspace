# Fast Thread Crawler - Performance Guide

## Overview

The `fast_thread_crawler.py` is an optimized version that uses parallel processing to crawl threads much faster than the sequential crawler.

## Speed Comparison

| Method | Workers | Delay | Threads/Hour | Use Case |
|--------|---------|-------|--------------|----------|
| `reddit_thread_crawler.py` | 1 | 15-30s | ~120-240 | Safe, sequential |
| `fast_thread_crawler.py --speed slow` | 1 | 10-20s | ~180-360 | Safe, sequential |
| `fast_thread_crawler.py --speed medium` | 3 | 3-6s | ~1800-3600 | **Recommended** |
| `fast_thread_crawler.py --speed fast` | 5 | 1-3s | ~6000-18000 | Fast, watch rate limits |
| `fast_thread_crawler.py --speed aggressive` | 10 | 0.5-1.5s | ~24000-72000 | Very fast, may hit limits |

## Quick Start

### Basic Usage (Recommended)

```bash
docker compose exec jupyterlab python fast_thread_crawler.py \
    --seed "https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/" \
    --speed medium \
    --max-threads 100
```

### Multiple Seeds

```bash
docker compose exec jupyterlab python fast_thread_crawler.py \
    --seed "https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/" \
    --seed "https://www.reddit.com/r/SillyTavernAI/comments/1pu1nx1/looks_like_glm_47_cares_about_us/" \
    --speed medium \
    --max-threads 200
```

### From File

Create `seeds.txt`:
```
https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/
https://www.reddit.com/r/SillyTavernAI/comments/1pu1nx1/looks_like_glm_47_cares_about_us/
```

Then:
```bash
docker compose exec jupyterlab python fast_thread_crawler.py \
    --seeds-file seeds.txt \
    --speed medium \
    --max-threads 500
```

## Features

### 1. Parallel Processing

Crawls multiple threads simultaneously using ThreadPoolExecutor:
- Default: 3 workers (medium speed)
- Configurable: 1-10+ workers
- Automatic queue management

### 2. Resume Capability

Automatically skips already-crawled threads:
- Checks Neo4j for existing posts
- Saves progress periodically
- Can resume interrupted crawls

### 3. Smart Queue Management

- Automatically discovers related threads from comments
- Adds them to queue for crawling
- Deduplicates to avoid re-crawling

### 4. Progress Tracking

- Real-time statistics
- Progress saved to `crawl_progress.json`
- Shows: crawled, skipped, errors, relationships

## Speed Presets

### Slow (Safe)
```bash
--speed slow
```
- 1 worker
- 10-20 second delays
- ~180-360 threads/hour
- Use when: Being extra careful with rate limits

### Medium (Recommended)
```bash
--speed medium
```
- 3 workers
- 3-6 second delays
- ~1800-3600 threads/hour
- Use when: Normal crawling, good balance

### Fast
```bash
--speed fast
```
- 5 workers
- 1-3 second delays
- ~6000-18000 threads/hour
- Use when: Need speed, monitor for rate limits

### Aggressive
```bash
--speed aggressive
```
- 10 workers
- 0.5-1.5 second delays
- ~24000-72000 threads/hour
- Use when: Maximum speed, may hit rate limits

## Custom Configuration

Override preset values:

```bash
docker compose exec jupyterlab python fast_thread_crawler.py \
    --seed "https://..." \
    --workers 8 \
    --delay-min 2.0 \
    --delay-max 4.0 \
    --max-threads 1000
```

## Examples

### Example 1: Quick Test (10 threads)

```bash
docker compose exec jupyterlab python fast_thread_crawler.py \
    --seed "https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/" \
    --speed medium \
    --max-threads 10
```

### Example 2: Large Crawl (1000 threads)

```bash
docker compose exec jupyterlab python fast_thread_crawler.py \
    --seed "https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/" \
    --speed fast \
    --max-threads 1000
```

### Example 3: Multiple Subreddits

```bash
# Create seeds file with multiple threads
cat > seeds.txt << EOF
https://old.reddit.com/r/LocalLLaMA/comments/1ptxm3x/ama_with_zai_the_lab_behind_glm47/
https://www.reddit.com/r/SillyTavernAI/comments/1pu1nx1/looks_like_glm_47_cares_about_us/
EOF

docker compose exec jupyterlab python fast_thread_crawler.py \
    --seeds-file seeds.txt \
    --speed medium \
    --max-threads 500
```

## Rate Limit Considerations

Reddit's public API is generally permissive, but:

1. **Start Slow**: Use `--speed slow` or `medium` initially
2. **Monitor**: Watch for errors indicating rate limits
3. **Back Off**: If you see 429 errors, reduce workers or increase delays
4. **User-Agent**: Make sure you have a proper User-Agent set in `.env`

## Progress and Resume

### Check Progress

Progress is saved to `data/reddit_threads/fast/crawl_progress.json`:

```bash
cat data/reddit_threads/fast/crawl_progress.json
```

### Resume Interrupted Crawl

The crawler automatically resumes by checking Neo4j. If you want to force re-crawl:

```bash
--no-resume  # Don't skip already-crawled threads
```

## Output

### JSON Files

Each thread is saved to:
```
data/reddit_threads/fast/thread_{post_id}.json
```

### Neo4j Storage

All threads and relationships are stored in Neo4j automatically.

### Statistics

At the end of the crawl, you'll see:
```
CRAWL COMPLETE
Total crawled: 100
Total skipped: 5
Total errors: 2
Total relationships: 450
Elapsed time: 120.5s (2.0m)
Average time per thread: 1.2s
```

## Comparison with Sequential Crawler

| Feature | Sequential (`reddit_thread_crawler.py`) | Fast (`fast_thread_crawler.py`) |
|---------|----------------------------------------|--------------------------------|
| Speed | Slow (1 thread at a time) | Fast (parallel) |
| Workers | 1 | 1-10+ |
| Resume | Manual | Automatic |
| Queue | No | Yes |
| Progress | Basic | Detailed |
| Use Case | Small crawls, testing | Large crawls, production |

## Best Practices

1. **Start Small**: Test with `--max-threads 10` first
2. **Use Medium Speed**: `--speed medium` is usually safe
3. **Monitor Progress**: Check `crawl_progress.json` periodically
4. **Watch for Errors**: If you see many errors, slow down
5. **Use Resume**: Let it skip already-crawled threads automatically

## Troubleshooting

### Too Many Errors

Reduce speed or workers:
```bash
--speed slow --workers 1
```

### Too Slow

Increase speed (carefully):
```bash
--speed fast --workers 5
```

### Memory Issues

Reduce workers:
```bash
--workers 2
```

### Rate Limit Errors

Increase delays:
```bash
--delay-min 5.0 --delay-max 10.0
```






