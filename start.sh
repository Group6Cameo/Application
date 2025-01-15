#!/bin/bash

REPO_DIR="/home/aoyamaxx/Desktop/Repos"

# Activate virtual environment
source $REPO_DIR/cameo/bin/activate

# Run the application
python -m rpi_control.launcher

