#!/bin/bash

# Configuration
DATA_DIR="./data"
DUMPS_DIR="./dumps"

# Create dumps directory if it doesn't exist
mkdir -p "$DUMPS_DIR"

# Check if data directory exists and has files
if [ ! -d "$DATA_DIR" ] || [ -z "$(ls -A $DATA_DIR 2>/dev/null)" ]; then
    echo "Error: Data directory '$DATA_DIR' does not exist or is empty."
    echo "Please run the scraper first."
    exit 1
fi

# Generate timestamp for the dump file name
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP_FILENAME="reddit_data_dump_$TIMESTAMP.tar.gz"
DUMP_PATH="$DUMPS_DIR/$DUMP_FILENAME"

echo "Creating data dump: $DUMP_FILENAME"

# Create the tar.gz archive. We change to the parent directory and tar the data directory
# to ensure the archive only contains the 'data/' directory at the root.
tar -czf "$DUMP_PATH" "$DATA_DIR"

if [ $? -eq 0 ]; then
    echo "Dump created successfully at: $DUMP_PATH"
    echo "Dump size: $(du -sh "$DUMP_PATH" | awk '{print $1}')"
else
    echo "Error: Failed to create dump file."
    exit 1
fi
