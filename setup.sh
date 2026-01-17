#!/bin/bash

# setup.sh - Environment setup script for Linux/macOS

set -e

echo "=========================================="
echo "Setting up Flask Security Audit Environment"
echo "=========================================="

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating required directories..."
mkdir -p config logs

# Set environment variables (optional - for testing)
export FLASK_ENV=production
export FLASK_APP=input.py
export PAYMENT_TOKEN="test_token_12345"
export MAIL_SERVER_KEY="test_mail_key"
export INTERNAL_AUTH="test_internal_key"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To activate the environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run the application:"
echo "  python input.py"
echo ""
echo "To run tests:"
echo "  bash run_test.sh"
echo ""
echo "To run automatic environment detection and testing:"
echo "  python auto_test.py"
echo ""
