#!/bin/bash

# Exit on any error
set -e

# Script version for tracking changes and config manager setup.
SRIPT_VERSION="1.0.0"
VENV_DIR=".venv"
CONFIG_MANAGER_DIR="/var/lib/config-manager"
CONFIG_MANAGER_LOG="/var/log/config-manager"
REQUIREMENTS_FILE="requirements.txt"
VENV_MARKER=".venv/.bootstrapped"

echo "Starting Git Sync Manager setup..."

# Set up config manager directories and permissions
setup_config_manager() {
    echo "Setting up config manager directories and permissions..."
    
    # Create config manager group
    # Creating a new group and adding user to it to manage permissions.
    # TODO : Need more robust user management.
    sudo groupadd -f config-manager
    
    # Create and set up config manager directories
    sudo mkdir -p "$CONFIG_MANAGER_DIR"
    sudo mkdir -p "$CONFIG_MANAGER_LOG"
    
    # Set directory permissions
    sudo chown root:config-manager "$CONFIG_MANAGER_DIR"
    sudo chmod 775 "$CONFIG_MANAGER_DIR"
    
    sudo chown root:config-manager "$CONFIG_MANAGER_LOG"
    sudo chmod 775 "$CONFIG_MANAGER_LOG"
    
    # Create and initialize state file with empty JSON object
    echo '{}' | sudo tee "$CONFIG_MANAGER_DIR/state.json" > /dev/null
    sudo chown root:config-manager "$CONFIG_MANAGER_DIR/state.json"
    sudo chmod 664 "$CONFIG_MANAGER_DIR/state.json"
    
    # Add current user to config-manager group
    if [ ! -z "$SUDO_USER" ]; then
        sudo usermod -a -G config-manager "$SUDO_USER"
        echo "Added $SUDO_USER to config-manager group"
    else
        echo "Warning: Could not determine sudo user. Please manually add users to config-manager group"
    fi
}

# Function to install system packages
install_system_packages() {
    echo "Installing required system packages..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv git pkg-config libsystemd-dev
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
# Facing issues in ubuntu 22.04 if venv is not removed first.
if [ -d ".venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf .venv
fi

# Create new virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate



# Set up config manager
setup_config_manager

# Install requirements using the full path to pip
echo "Installing dependencies..."
.venv/bin/pip install -r requirements.txt

echo "Setup complete! You can now run the sync manager using:"
echo "source .venv/bin/activate"
echo "python3 src.sync_manager.py --help"
echo "python3 src.config_manager.py --help"
