#!/bin/bash
# Helper script for managing nightly imageboard packs

set -e

PACKS_DIR="${PACKS_DIR:-packs}"
UNPACKED_DIR="${UNPACKED_DIR:-unpacked}"
ARCHIVE_DIR="${ARCHIVE_DIR:-archive}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_usage() {
    cat << EOF
Usage: $0 <command> [args]

Commands:
  create [--full] [name]  Create a new nightly pack (default: today's date)
  unpack <spec>           Unpack pack by path or timestamp
  unpack-latest           Unpack latest pack
  list                    List all available packs
  archive-days <N>        Move packs older than N days to archive
  clean-unpacked          Remove all unpacked directories
  show <spec>             Show pack metadata without unpacking
  size <spec>             Show pack size
  compare <spec1> <spec2> Compare two packs

Timestamp formats for unpack/show/size:
  YYYY-MM-DD              Exact date (e.g., 2026-01-02)
  YYYYMMDD                Short date (e.g., 20260102)
  latest                  Most recent pack
  today                   Today's pack
  yesterday               Yesterday's pack
  "N days ago"            Relative time (e.g., "3 days ago")

Examples:
  $0 create                      # Create pack for today
  $0 create custom-name          # Create pack with custom name
  $0 unpack latest               # Unpack latest pack
  $0 unpack "3 days ago"         # Unpack pack from 3 days ago
  $0 list                        # List all packs
  $0 archive-days 30             # Archive packs older than 30 days
  $0 compare yesterday today      # Compare yesterday vs today

Environment variables:
  PACKS_DIR              Directory for packs (default: packs)
  UNPACKED_DIR           Directory for unpacked data (default: unpacked)
  ARCHIVE_DIR            Directory for archived packs (default: archive)
EOF
}

command_create() {
    local name="${1:-nightly-$(date +%Y-%m-%d)}"
    local full=""
    
    if [ "$1" = "--full" ] || [ "$2" = "--full" ]; then
        full="--include-image-content"
        echo "Creating FULL pack (including images): $name"
    else
        echo "Creating pack: $name"
    fi
    
    python create_nightly_pack.py \
      --pack-name "$name" \
      --output-dir "$PACKS_DIR" \
      $full
}

command_unpack() {
    local spec="$1"
    if [ -z "$spec" ]; then
        echo "Error: specification required"
        echo "Usage: $0 unpack <spec>"
        exit 1
    fi
    echo "Unpacking pack: $spec"
    python unpack_nightly_pack.py \
      "$spec" \
      --output-dir "$UNPACKED_DIR" \
      --packs-dir "$PACKS_DIR"
}

command_unpack_latest() {
    echo "Unpacking latest pack..."
    python unpack_nightly_pack.py \
      latest \
      --output-dir "$UNPACKED_DIR" \
      --packs-dir "$PACKS_DIR"
}

command_list() {
    echo "Available packs in: $PACKS_DIR"
    python unpack_nightly_pack.py --list --packs-dir "$PACKS_DIR"
}

command_archive_days() {
    local days="$1"
    if [ -z "$days" ]; then
        echo "Error: number of days required"
        echo "Usage: $0 archive-days <N>"
        exit 1
    fi

    echo "Archiving packs older than $days days..."
    mkdir -p "$ARCHIVE_DIR"

    local moved=0
    for pack in "$PACKS_DIR"/nightly-*.tar.gz; do
        if [ -f "$pack" ]; then
            if find "$pack" -mtime +"$days" -print -quit | grep -q .; then
                mv "$pack" "$ARCHIVE_DIR/"
                echo "  Archived: $(basename "$pack")"
                ((moved++))
            fi
        fi
    done

    echo "Archived $moved pack(s) to: $ARCHIVE_DIR"
}

command_clean_unpacked() {
    echo "Removing unpacked directories..."
    local removed=0
    for dir in "$UNPACKED_DIR"/nightly-*; do
        if [ -d "$dir" ]; then
            rm -rf "$dir"
            echo "  Removed: $(basename "$dir")"
            ((removed++))
        fi
    done
    echo "Removed $removed unpacked director(ies)"
}

command_show() {
    local spec="$1"
    if [ -z "$spec" ]; then
        echo "Error: specification required"
        echo "Usage: $0 show <spec>"
        exit 1
    fi

    local pack_path
    if [ -f "$spec" ]; then
        pack_path="$spec"
    else
        pack_path=$(python -c "
import sys
sys.path.insert(0, 'src')
from unpack_nightly_pack import find_pack_by_timestamp
from pathlib import Path
result = find_pack_by_timestamp(Path('$PACKS_DIR'), '$spec')
if result:
    print(result.absolute())
" 2>/dev/null)
    fi

    if [ -z "$pack_path" ] || [ ! -e "$pack_path" ]; then
        echo "Error: Pack not found: $spec"
        exit 1
    fi

    echo "Pack: $pack_path"
    echo ""

    if [ -f "$pack_path" ]; then
        local temp_dir="$PACKS_DIR/.temp_show"
        mkdir -p "$temp_dir"
        tar -xzf "$pack_path" -C "$temp_dir" metadata.json 2>/dev/null || true

        if [ -f "$temp_dir/metadata.json" ]; then
            cat "$temp_dir/metadata.json" | python -m json.tool
            rm -rf "$temp_dir"
        else
            echo "No metadata found in pack"
        fi
    elif [ -d "$pack_path" ]; then
        if [ -f "$pack_path/metadata.json" ]; then
            cat "$pack_path/metadata.json" | python -m json.tool
        else
            echo "No metadata found in pack directory"
        fi
    fi
}

command_size() {
    local spec="$1"
    if [ -z "$spec" ]; then
        echo "Error: specification required"
        echo "Usage: $0 size <spec>"
        exit 1
    fi

    local pack_path
    if [ -f "$spec" ]; then
        pack_path="$spec"
    else
        pack_path=$(python -c "
import sys
sys.path.insert(0, 'src')
from unpack_nightly_pack import find_pack_by_timestamp
from pathlib import Path
result = find_pack_by_timestamp(Path('$PACKS_DIR'), '$spec')
if result:
    print(result.absolute())
" 2>/dev/null)
    fi

    if [ -z "$pack_path" ] || [ ! -e "$pack_path" ]; then
        echo "Error: Pack not found: $spec"
        exit 1
    fi

    if [ -f "$pack_path" ]; then
        local size_bytes=$(stat -c%s "$pack_path")
        local size_mb=$((size_bytes / 1024 / 1024))
        echo "Pack: $(basename "$pack_path")"
        echo "Size: $size_mb MB ($size_bytes bytes)"
    elif [ -d "$pack_path" ]; then
        local size_bytes=$(du -sb "$pack_path" | cut -f1)
        local size_mb=$((size_bytes / 1024 / 1024))
        echo "Pack: $(basename "$pack_path")"
        echo "Size: $size_mb MB ($size_bytes bytes) (directory)"
    fi
}

command_compare() {
    local spec1="$1"
    local spec2="$2"
    if [ -z "$spec1" ] || [ -z "$spec2" ]; then
        echo "Error: two specifications required"
        echo "Usage: $0 compare <spec1> <spec2>"
        exit 1
    fi

    echo "Comparing packs: $spec1 vs $spec2"
    echo ""

    python -c "
import sys
sys.path.insert(0, 'src')
from unpack_nightly_pack import find_pack_by_timestamp
from pathlib import Path
import pandas as pd

packs_dir = Path('$PACKS_DIR')
pack1 = find_pack_by_timestamp(packs_dir, '$spec1')
pack2 = find_pack_by_timestamp(packs_dir, '$spec2')

if not pack1 or not pack2:
    print('Error: One or both packs not found')
    sys.exit(1)

# Find metadata files
def get_metadata(pack_path):
    if pack_path.is_file():
        import tarfile
        import tempfile
        import json
        import os
        with tarfile.open(pack_path, 'r:gz') as tar:
            for member in tar.getmembers():
                if member.name.endswith('metadata.json'):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        tar.extract(member, tmpdir)
                        meta_path = Path(tmpdir) / member.name
                        with open(meta_path) as f:
                            return json.load(f)
    elif pack_path.is_dir():
        import json
        meta_path = pack_path / 'metadata.json'
        if meta_path.exists():
            with open(meta_path) as f:
                return json.load(f)
    return {}

meta1 = get_metadata(pack1)
meta2 = get_metadata(pack2)

print(f'Pack 1: {pack1.name}')
print(f'  Created: {meta1.get(\"created_at\", \"unknown\")}')
print(f'  Threads: {meta1.get(\"thread_count\", 0)}')
print(f'  Images: {meta1.get(\"image_count\", 0)}')
if 'stats' in meta1:
    size_mb = meta1['stats'].get('total_size_bytes', 0) / (1024*1024)
    print(f'  Size: {size_mb:.1f} MB')
print()
print(f'Pack 2: {pack2.name}')
print(f'  Created: {meta2.get(\"created_at\", \"unknown\")}')
print(f'  Threads: {meta2.get(\"thread_count\", 0)}')
print(f'  Images: {meta2.get(\"image_count\", 0)}')
if 'stats' in meta2:
    size_mb = meta2['stats'].get('total_size_bytes', 0) / (1024*1024)
    print(f'  Size: {size_mb:.1f} MB')
print()

if 'image_count' in meta1 and 'image_count' in meta2:
    delta = meta2['image_count'] - meta1['image_count']
    if delta > 0:
        print(f'Pack 2 has {delta} more images')
    elif delta < 0:
        print(f'Pack 1 has {-delta} more images')
    else:
        print('Both packs have the same number of images')

if 'thread_count' in meta1 and 'thread_count' in meta2:
    delta = meta2['thread_count'] - meta1['thread_count']
    if delta > 0:
        print(f'Pack 2 has {delta} more threads')
    elif delta < 0:
        print(f'Pack 1 has {-delta} more threads')
    else:
        print('Both packs have the same number of threads')
"
}

main() {
    local command="$1"
    shift || true

    case "$command" in
        create)
            command_create "$@"
            ;;
        unpack)
            command_unpack "$@"
            ;;
        unpack-latest)
            command_unpack_latest
            ;;
        list)
            command_list
            ;;
        archive-days)
            command_archive_days "$@"
            ;;
        clean-unpacked)
            command_clean_unpacked
            ;;
        show)
            command_show "$@"
            ;;
        size)
            command_size "$@"
            ;;
        compare)
            command_compare "$@"
            ;;
        help|--help|-h)
            print_usage
            ;;
        *)
            if [ -z "$command" ]; then
                print_usage
            else
                echo "Error: Unknown command: $command"
                echo ""
                print_usage
                exit 1
            fi
            ;;
    esac
}

main "$@"
