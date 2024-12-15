#!/bin/bash

# Install dependencies and setup virtual environment
source rpi_control/utils/setup.sh

# Install the application
pip install -e .

# Setup display configuration
source scripts/setup_display.sh

# Install and enable the service
source scripts/install_service.sh

echo "Installation complete! The application will start on next boot."
echo "To start now without rebooting, run: sudo systemctl start rpi-control"