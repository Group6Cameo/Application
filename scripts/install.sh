#!/bin/bash

# Install dependencies and setup virtual environment
source rpi_control/utils/setup.sh

# Install the application
pip install -e .

# Setup display configuration
source scripts/setup_display.sh

# Install and enable the service
source scripts/install_service.sh

#install ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.tgz
sudo tar xvzf ./ngrok-v3-stable-linux-arm64.tgz -C /usr/local/bin
ngrok authtoken 2rZfVcXwEHVl8HlEft8imU7bvUL_3xnAT1AaKtUnNMdGzjTx1

sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-gstreamer-1.0 gir1.2-gst-plugins-base-1.0

echo "Installation complete! The application will start on next boot."
echo "To start now without rebooting, run: sudo systemctl start rpi-control"