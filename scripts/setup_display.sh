#!/bin/bash

# Enable auto-login for the pi user
sudo raspi-config nonint do_boot_behaviour B4

# Install required X server components if not present
sudo apt-get update
sudo apt-get install -y xserver-xorg x11-xserver-utils

# Create or update the auto-start configuration
mkdir -p /home/$USER/.config/autostart
cat << EOF > /home/$USER/.config/autostart/rpi-control.desktop
[Desktop Entry]
Type=Application
Name=RPI Control
Exec=rpi-control
EOF

# Set permissions
chmod +x /home/$USER/.config/autostart/rpi-control.desktop