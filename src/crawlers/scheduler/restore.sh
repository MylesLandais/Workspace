#!/bin/bash

# Configuration
DUMPS_DIR="./dumps"
DATA_DIR="./data"

echo "Starting data restore process."

# 1. Find the latest dump file
LATEST_DUMP=$(ls -t "$DUMPS_DIR"/reddit_data_dump_*.tar.gz 2>/dev/null | head -n 1)

if [ -z "$LATEST_DUMP" ]; then
    echo "Error: No dump files found in '$DUMPS_DIR'. Cannot restore."
    exit 1
fi

echo "Found latest dump file: $(basename "$LATEST_DUMP")"

# 2. Prepare the environment
# Create data directory if it doesn't exist (tar will also do this, but for clarity)
mkdir -p "$DATA_DIR"

# 3. Extract the dump
echo "Restoring data from $LATEST_DUMP..."

# Check if the existing data directory is not empty and confirm overwrite
if [ -n "$(ls -A $DATA_DIR 2>/dev/null)" ]; then
    read -r -p "Warning: '$DATA_DIR' is not empty. Overwrite its contents? (y/N) " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            echo "Proceeding with restore..."
            # Remove old data to ensure a clean restore
            rm -rf "$DATA_DIR"/*
            ;;
        *)
            echo "Restore cancelled by user."
            exit 0
            ;;
    esac
fi

# Extract the archive. The dump is expected to contain a directory named 'data/'
tar -xzf "$LATEST_DUMP" -C .

if [ $? -eq 0 ]; then
    echo "Restore successful!"
    echo "Restored files are now in the '$DATA_DIR' directory."
else
    echo "Error: Failed to extract dump file."
    exit 1
fi
