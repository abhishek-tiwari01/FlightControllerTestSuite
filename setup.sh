#!/bin/bash

# Ensure the script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root"
    exit 1
fi

# Update and install required system packages
echo "Updating system and installing required packages..."
apt-get update && apt-get install -y \
    python3-dev \
    python3-opencv \
    python3-wxgtk4.0 \
    python3-pip \
    python3-matplotlib \
    python3-lxml \
    python3-pygame \
    adb \
    usbutils \
    can-utils

# Install Python dependencies for the current user
echo "Installing Python dependencies for the current user..."
pip3 install --user --no-cache-dir PyYAML mavproxy jinja2 weasyprint pyserial colorama pymavlink

# Add current user to dialout group
echo "Adding user to dialout group..."
usermod -a -G dialout $SUDO_USER

# Ensure ModemManager is disabled
echo "Disabling ModemManager..."
systemctl disable ModemManager.service
systemctl stop ModemManager.service

echo "Setup completed successfully. The system is ready for flight controller testing."
