#!/bin/bash

# Exit on any error
set -e

# Script version for tracking changes
SCRIPT_VERSION="1.0.0"
VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"
VENV_MARKER=".venv/.bootstrapped"

echo "Starting Git Sync Manager setup..."

# Function to install system packages
install_system_packages() {
    echo "Installing required system packages..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv git
}

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Installing..."
    install_system_packages
fi

# Check if pip module is available
if ! python3 -c "import pip" &> /dev/null; then
    echo "Python3-pip is not installed. Installing..."
    install_system_packages
fi

# Check if python3-venv is installed
if ! dpkg -l | grep -q python3-venv; then
    echo "Python3-venv is not installed. Installing..."
    sudo apt-get update && sudo apt-get install -y python3-venv
fi

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Installing..."
    sudo apt-get update && sudo apt-get install -y git
fi

# Remove existing virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf .venv
fi

# Create new virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv --without-pip

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Download and install pip in the virtual environment
echo "Setting up pip in virtual environment..."
curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py --no-warn-script-location
rm get-pip.py

# Install requirements using the full path to pip
echo "Installing dependencies..."
.venv/bin/pip install -r requirements.txt

echo "Setup complete! You can now run the sync manager using:"
echo "source .venv/bin/activate"
echo "python3 sync_manager.py --help"
