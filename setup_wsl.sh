#!/bin/bash

# This is targeted toward 'Ubuntu-24.04' WSL 2
# Don't forget to 'chmod +x setup_wsl.sh'

# Exit on error
set -e

echo "Installing dependencies..."
sudo apt update
sudo apt install -y \
  pkg-config \
  cmake \
  libglib2.0-dev \
  libadwaita-1-dev \
  libgtk-4-dev \
  blueprint-compiler

echo "Creating symbolic link for Wayland support..."
WAYLAND_DIR="/mnt/wslg/runtime-dir/wayland-0*"
USER_RUN_DIR="/run/user/$(id -u)"

# Check if the Wayland directory exists
if [ -d "$WAYLAND_DIR" ]; then
  ln -s "$WAYLAND_DIR" "$USER_RUN_DIR/"
  echo "Wayland symbolic link created at $USER_RUN_DIR"
else
  echo "Wayland directory not found, skipping symbolic link creation."
fi

echo "Setup complete!"
