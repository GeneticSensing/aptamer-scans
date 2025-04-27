#!/bin/bash

# Install required system package
sudo apt update
sudo apt install -y python3-libgpiod

# Create a Python virtual environment
python3 -m venv --system-site-packages my-venv

# Activate the virtual environment
source my-venv/bin/activate

# Install Python packages from requirements.txt
pip3 install -r requirements.txt
