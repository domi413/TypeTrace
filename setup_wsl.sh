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
  blueprint-compiler \
  meson

echo "Creating symbolic link for Wayland support..."

ln -s /mnt/wslg/runtime-dir/wayland-0* /run/user/$(id -u)/

echo "Setup complete!"
