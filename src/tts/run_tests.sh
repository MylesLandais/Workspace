#!/usr/bin/env bash
#
# run_tests.sh
# 
# Runs the TTS comparison/test scripts within a Nix shell capable of running
# the python environment (handling libstdc++ and zlib issues).
#
# Usage:
#   ./run_tests.sh [target]
#   ./run_tests.sh moss
#   ./run_tests.sh qwen
#

set -e

# Ensure we are in the directory of the script
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Error: .venv not found. Please run 'uv venv .venv' and install dependencies first."
    exit 1
fi

echo "--- Starting Nix Shell for TTS Testing ---"
export NIXPKGS_ALLOW_UNFREE=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Command to run inside the nix-shell
if [[ "$1" == *.py ]]; then
    SCRIPT="$1"
    shift
else
    SCRIPT="compare_tts.py"
fi

# Define the shell environment with unfree packages allowed (CUDA)
# FIX: Do NOT include cudaPackages.cudatoolkit in buildInputs. It conflicts with the host driver.
# We MUST explicitly point to /run/opengl-driver/lib to find the host's libcuda.so.
EXPR='with import <nixpkgs> { config = { allowUnfree = true; }; }; mkShell {
  buildInputs = [
    stdenv.cc.cc.lib
    zlib
    glib
    # linuxPackages.nvidia_x11 # Optional, sometimes helps, but host path is key
  ];
  shellHook = "export LD_LIBRARY_PATH=/run/opengl-driver/lib:${lib.makeLibraryPath [ stdenv.cc.cc.lib zlib glib ]}:$LD_LIBRARY_PATH";
}'

# Execute inside the shell
CMD="source .venv/bin/activate && python $SCRIPT $@"

nix-shell -E "$EXPR" --run "$CMD"
