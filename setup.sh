#!/bin/bash

# Install Python if not present
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found. Installing..."
    # For Ubuntu/Debian
    sudo apt-get update && sudo apt-get install -y python3 python3-pip
fi

# Install dependencies
pip3 install -r requirements.txt

echo "Setup complete."