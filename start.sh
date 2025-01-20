#!/bin/bash

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    pkill -f "python -m rpi_control.launcher"
    pkill ngrok
    sudo fuser -k 8000/tcp
}

# Register cleanup function
trap cleanup EXIT

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

# Activate virtual environment if not already activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    source $REPO_DIR/cameo/bin/activate
fi

# Run the application
python -m rpi_control.launcher

# Wait for cleanup
wait

