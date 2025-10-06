# Config Manager

> A lightweight, Python-based configuration management system using YAML cookbooks with Git synchronization

## Overview

Config Manager is a simple yet powerful tool for managing Linux system configurations. It uses human-readable YAML files (cookbooks) to define desired system states and automatically applies changes while maintaining idempotency.

## Key Features

- **Pure Python** - No complex dependencies, easy to understand and extend
- **Package Management** - Install/remove system packages via apt
- **File Management** - Deploy configuration files with proper ownership and permissions  
- **Service Management** - Control systemd services (start, stop, restart, enable/disable)
- **Git Synchronization** - Auto-sync cookbooks from remote repositories
- **Idempotent Operations** - Only apply changes when needed, safe to run repeatedly
- **State Tracking** - Maintains checksums to detect configuration changes

## Quick Start

1. **Clone and Setup:**
   ```bash
   git clone https://github.com/susantomahato/config-manager.git
   cd config-manager
   sudo ./bootstrap.sh  # Sets up everything automatically
   ```

2. **Apply Configuration:**
   ```bash
   python3 src/config_manager.py  # Apply all cookbooks
   ```

3. **Start Git Sync (Optional):**
   ```bash
   python3 src/sync_service.py --once  # Sync once, or remove --once for continuous
   ```

## Project Structure

```
config-manager/
├── src/                     # Source code
│   ├── config_manager.py    #   Core configuration management
│   ├── sync_service.py      #   Git repository sync service  
│   └── constants.py         #   Configuration constants
├── cookbooks/               # YAML configuration cookbooks
│   └── webserver.yaml      #   Example: NGINX + PHP-FPM setup
├── tests/                   # Unit tests
│   ├── test_config_manager.py
│   ├── test_sync_service.py
│   └── run_tests.py         #   Unified test runner
├── requirements.txt         # Python dependencies
├── setup.py                 # Package installation
├── bootstrap.sh             # Automated setup script
└── README.md               # This documentation
```

## Installation

### Requirements

- **OS**: Linux (Ubuntu/Debian recommended)
- **Python**: 3.6+ 
- **Privileges**: sudo access for system configuration

### Installation Methods

#### Recommended: Bootstrap Script
```bash
git clone https://github.com/susantomahato/config-manager.git
cd config-manager
sudo ./bootstrap.sh
```
*Handles everything automatically: system packages, Python environment, permissions*


#### Manual Setup
```bash
# Install system dependencies
sudo apt-get update && sudo apt-get install -y \
    python3 python3-pip python3-venv git pkg-config libsystemd-dev

# Create Python environment  
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Setup directories and permissions
sudo mkdir -p /var/lib/config-manager /var/log/config-manager
sudo groupadd -f config-manager  
sudo usermod -a -G config-manager $USER
```

## Usage

### Basic Commands

### Git Synchronization  

```bash
# Sync once and exit
python3 src/sync_service.py --once

# Continuous sync (5-minute intervals)  
python3 src/sync_service.py

```bash
# Apply all cookbooks in cookbooks/ directory
python3 src/config_manager.py

# Use specific directory  
python3 src/config_manager.py --config-dir /path/to/cookbooks

# Enable debug output
python3 src/config_manager.py --debug
```



# Custom configuration
python3 src/sync_service.py \
    --repo-url https://github.com/your-org/configs.git \
    --local-path /var/lib/config-manager/repo \
    --branch production \
    --interval 10
```

### Production Deployment

**Option 1: Cron Job**
```bash
# Edit crontab: crontab -e
# Run every hour
0 * * * * cd /path/to/config-manager && source .venv/bin/activate && python3 src/config_manager.py
```

**Option 2: Systemd Service**
```bash
# Create service files for both components
sudo systemctl enable config-manager.service
sudo systemctl enable config-sync.service  
```

### CLI Tools (After Package Installation)

```bash
config-manager --config-dir cookbooks/ --debug
config-sync --repo-url https://github.com/user/configs.git --once
```

## YAML Cookbook Format

Cookbooks are YAML files that define the desired system state. Here's the structure:

### Example Cookbook

**Basic Web Server Setup** (`cookbooks/webserver.yaml`):
```yaml
name: "Web Server Configuration"
version: "1.0.0"

install:
  pre_install:
    - command: "/usr/bin/apt-get update"
      sudo: true
  install:
    - package: nginx
      state: present
    - package: php-fpm
      state: present

configure:
  files:
    - path: /var/www/html/index.html
      content: |
        <h1>Welcome to Config Manager!</h1>
        <p>Server configured automatically</p>
      owner: www-data
      group: www-data
      mode: "0644"
  
  services:
    - name: nginx
      state: started
      enabled: true
    - name: php8.1-fpm  
      state: started
      enabled: true
```

**More Examples:**
- See `cookbooks/webserver.yaml` for complete NGINX + PHP setup

## Configuration Options

### Environment Variables

- `DEFAULT_REPO_URL`: Git repository URL for cookbooks
- `DEFAULT_LOCAL_PATH`: Local path for synchronized repository
- `DEFAULT_BRANCH`: Git branch to track
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)

### State Management

The system maintains state in `/var/lib/config-manager/state.json` to ensure idempotent operations. This file tracks:
- Configuration file checksums
- Last applied configurations
- System state information

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/susantomahato/config-manager.git
cd config-manager

### Testing

```bash
# Run all tests (recommended)
python3 tests/run_tests.py

# Individual test files  
python3 tests/test_config_manager.py
python3 tests/test_sync_service.py
```

### Package Building

```bash
# Build distributable package
python3 -m build

# Install built package
pip install dist/config_manager-1.0.0-py3-none-any.whl

# Verify installation  
pip show config-manager
```

### Adding New Cookbooks

1. Create a new YAML file in the `cookbooks/` directory
2. Follow the cookbook format described above
3. Test with `python3 src/config_manager.py --config-dir cookbooks/`

## Troubleshooting

| Issue | Solution |  
|-------|----------|
| **Permission Denied** | • Add user to `config-manager` group<br>• Re-login after bootstrap script<br>• Check `/var/lib/config-manager` ownership |
| **Git Sync Fails** | • Verify repository URL and credentials<br>• Test network connectivity<br>• Ensure git is configured properly |  
| **Package Errors** | • Run `sudo apt-get update`<br>• Check for package conflicts<br>• Review logs with `--debug` flag |
| **Service Issues** | • Check `journalctl -u service-name`<br>• Verify systemd service files<br>• Test manual service commands |

### Debugging & Logs

```bash
# Enable verbose logging
python3 src/config_manager.py --debug

# Check application logs  
tail -f /var/log/config-manager/config-manager.log

# System service logs
journalctl -u config-manager -f
```

