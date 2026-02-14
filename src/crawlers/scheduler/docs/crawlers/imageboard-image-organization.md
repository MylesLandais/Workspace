# 4chan Image Organization

## Overview

Images are now organized by board and thread for better structure and easier navigation.

## Directory Structure

### New Organized Structure
```
cache/4chan/images/
├── {board}/              # e.g., 'b', 'pol', 'g'
│   └── {thread_id}/      # e.g., '944153883'
│       ├── {hash}.jpg
│       ├── {hash}.png
│       └── {hash}.webm
└── {hash}.{ext}          # Symlinks for backward compatibility
```

### Benefits

1. **Organized by Context**: Images are grouped by board and thread, making it easy to find all images from a specific thread
2. **Deduplication**: Same image hash is stored once, but organized by where it was first seen
3. **Backward Compatibility**: Symlinks in the flat directory allow existing tools to find images by hash
4. **Scalability**: As you monitor more threads, images stay organized automatically

## Usage

### Automatic Organization

New images are automatically organized when downloaded by the monitor. The structure is created as:
- `images/{board}/{thread_id}/{hash}.{ext}`

### Organizing Existing Images

To organize existing images from the flat structure:

```bash
# Dry run first to see what would be organized
docker exec jupyter python /home/jovyan/workspace/organize_4chan_images.py --dry-run

# Actually organize the images
docker exec jupyter python /home/jovyan/workspace/organize_4chan_images.py
```

This script:
- Reads image mappings from Neo4j (which threads images belong to)
- Moves images to organized structure
- Creates symlinks for backward compatibility

## Finding Images

### By Thread
```bash
# View all images from a specific thread
docker exec jupyter ls -lh /home/jovyan/workspace/cache/4chan/images/b/944153883
```

### By Board
```bash
# View all threads on a board
docker exec jupyter ls /home/jovyan/workspace/cache/4chan/images/b
```

### By Hash (Backward Compatible)
```bash
# Still works via symlink
docker exec jupyter ls -lh /home/jovyan/workspace/cache/4chan/images/{hash}.jpg
```

## Querying from Neo4j

You can also query images by thread from Neo4j:

```cypher
// Get all images from a specific thread
MATCH (t:Thread {board: 'b', thread_id: 944153883})<-[:POSTED_IN]-(p:Post)
WHERE p.image_hash IS NOT NULL
RETURN p.image_hash, p.image_url, p.image_path
ORDER BY p.post_no
```

## Migration Notes

- Existing images in the flat structure remain accessible
- New images are automatically organized
- Run `organize_4chan_images.py` to migrate existing images when ready
- Symlinks ensure backward compatibility with existing tools



