#!/bin/bash

echo "Moving Gopher files to proper location..."

# Create the target directory structure
mkdir -p Datasets/go-gophers/scripts/

# Move the download script
echo "Moving download_gophers.py..."
mv "Gopher Stuff/download_gophers.py" "Datasets/go-gophers/scripts/"

# Move the entire gopher_art directory to the datasets location
echo "Moving gopher artwork..."
mv "Gopher Stuff/gopher_art" "Datasets/go-gophers/"

# Remove the now-empty Gopher Stuff directory
echo "Cleaning up old directory..."
rmdir "Gopher Stuff"

echo "Gopher files successfully moved to Datasets/go-gophers/"
echo "Structure:"
echo "  Datasets/go-gophers/scripts/download_gophers.py"
echo "  Datasets/go-gophers/gopher_art/artwork/..."

# Clean up this script
rm -f move_gophers.sh

echo "Move completed!"