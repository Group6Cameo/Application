#!/bin/bash

# Get the repository directory (parent of script directory)
REPO_DIR="$(realpath "$(dirname "$0")/..")"

# Check if directory exists
if [ ! -d "$REPO_DIR" ]; then
    echo "Error: Repository directory not found: $REPO_DIR"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$REPO_DIR/cameo/bin" ]; then
    echo "Error: Virtual environment not found in $REPO_DIR/cameo"
    exit 1
fi

# Activate virtual environment
source $REPO_DIR/cameo/bin/activate

# Run the application
python -m rpi_control.launcher

