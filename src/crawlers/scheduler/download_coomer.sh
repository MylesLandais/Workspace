#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOWNLOADS_DIR="${SCRIPT_DIR}/downloads"
CREATORS_FILE="${SCRIPT_DIR}/coomer_creators.json"

usage() {
    cat <<EOF
Coomer.st Batch Downloader

Usage: $0 <command> [options]

Commands:
    list                    List available creators from config
    download <creator>      Download all posts for a creator
    download-one <url>      Download a single post URL
    incremental <creator>   Download only new posts
    all                     Download all creators
    stats                   Show download statistics

Options:
    --max-posts N           Maximum posts to download (default: 10)
    --offset N              Starting offset (default: 0)

Examples:
    $0 list
    $0 download myla.feet --max-posts 5
    $0 download-one "https://coomer.st/onlyfans/user/myla.feet/post/1507285131"
    $0 incremental myla.feet
    $0 all --max-posts 3

EOF
    exit 1
}

run_downloader() {
    docker run --rm \
        -v "${DOWNLOADS_DIR}:/home/warby/Workspace/jupyter/downloads" \
        -v "${SCRIPT_DIR}/coomer_batch_downloader.py:/script.py:ro" \
        -v "${CREATORS_FILE}:/creators.json:ro" \
        --network host \
        python:3.11-slim \
        sh -c "pip install requests beautifulsoup4 -q && python /script.py $1"
}

case "$1" in
    list)
        run_downloader "--list-creators --config /creators.json"
        ;;
    download)
        if [ -z "$2" ]; then
            echo "Error: Creator name required"
            usage
        fi
        shift
        ARGS="--creator $1 --api --config /creators.json"
        shift
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --max-posts)
                    ARGS="${ARGS} --max-posts $2"
                    shift 2
                    ;;
                --offset)
                    ARGS="${ARGS} --offset $2"
                    shift 2
                    ;;
                *)
                    ARGS="${ARGS} $1"
                    shift
                    ;;
            esac
        done
        run_downloader "${ARGS}"
        ;;
    download-one)
        if [ -z "$2" ]; then
            echo "Error: URL required"
            usage
        fi
        run_downloader "--creator unknown --posts $2 --max-posts 1"
        ;;
    incremental)
        if [ -z "$2" ]; then
            echo "Error: Creator name required"
            usage
        fi
        run_downloader "--incremental --creator $2 --config /creators.json --max-posts ${3:-10}"
        ;;
    all)
        shift
        ARGS="--all --config /creators.json --api"
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --max-posts)
                    ARGS="${ARGS} --max-posts $2"
                    shift 2
                    ;;
                *)
                    ARGS="${ARGS} $1"
                    shift
                    ;;
            esac
        done
        run_downloader "${ARGS}"
        ;;
    stats)
        echo "Download Statistics:"
        echo ""
        if [ -d "${DOWNLOADS_DIR}/metadata" ]; then
            for f in "${DOWNLOADS_DIR}/metadata/"*_gallery.json; do
                if [ -f "$f" ]; then
                    name=$(basename "$f" _gallery.json)
                    posts=$(python3 -c "import json; print(json.load(open('$f'))['posts'])" 2>/dev/null || echo "?")
                    media=$(python3 -c "import json; print(json.load(open('$f'))['total_media'])" 2>/dev/null || echo "?")
                    echo "  @${name}: ${posts} posts, ${media} files"
                fi
            done
        else
            echo "  No downloads found"
        fi
        ;;
    *)
        usage
        ;;
esac
