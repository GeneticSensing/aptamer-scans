#!/bin/bash

# Install required system package
sudo apt update
sudo apt install -y python3-libgpiod

# Create a Python virtual environment if it doesn't exist
if [ ! -d "my-venv" ]; then
    python3 -m venv --system-site-packages my-venv
fi

# Activate the virtual environment
source my-venv/bin/activate

# Install Python packages from requirements.txt
pip3 install -r requirements.txt

# After this point, the virtual environment stays activated in your terminal
echo "Setup complete. Virtual environment is now activated."
