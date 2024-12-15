#!/bin/bash

# Create systemd service file for your application
cat << EOF | sudo tee /etc/systemd/system/rpi-control.service
[Unit]
Description=RPI Control Application
After=network.target
After=multi-user.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$USER/.Xauthority
Environment=PYTHONUNBUFFERED=1
# Print network info before starting
ExecStartPre=$(which python) -c "from rpi_control.utils.network_info import print_network_info; print_network_info()"
ExecStart=$(which python) -m rpi_control.launcher
Restart=always
RestartSec=3

[Install]
WantedBy=graphical.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable rpi-control
sudo systemctl start rpi-control