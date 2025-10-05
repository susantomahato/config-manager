# Configuration Manager

A Python-based configuration management system that uses YAML cookbooks to manage packages, files, and services across Linux systems. The system provides git-based synchronization and idempotent configuration management.

## Features

- **Package Management**: Install and remove system packages
- **File Management**: Deploy configuration files with proper ownership and permissions
- **Service Management**: Control systemd services (start, stop, restart, enable/disable)
- **Git Synchronization**: Automatically sync configuration cookbooks from a remote repository
- **Idempotent Operations**: Only apply changes when configuration differs from current state
- **State Tracking**: Maintains state to avoid unnecessary reconfigurations

## Project Structure

```
config-manager/
├── src/
│   ├── config_manager.py    # Main configuration management logic
│   ├── sync_service.py      # Git repository synchronization service
│   └── constants.py         # Configuration constants
├── cookbooks/               # YAML configuration files
│   └── webserver.yaml      # Example web server configuration
├── tests/                   # Test files
├── docs/                    # Documentation
├── requirements.txt         # Python dependencies
├── bootstrap.sh            # Setup script
└── README.md               # This file
```

## Installation

### Prerequisites

- Linux system (Ubuntu/Debian recommended)
- Python 3.6 or higher
- sudo privileges for system configuration

### Quick Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/susantomahato/config-manager.git
   cd config-manager
   ```

2. **Run the bootstrap script:**
   ```bash
   sudo ./bootstrap.sh
   ```

   The bootstrap script will:
   - Install required system packages (Python 3, pip, venv, git)
   - Create a Python virtual environment
   - Install Python dependencies
   - Set up config-manager directories and permissions
   - Create necessary user groups

3. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

### Manual Installation

If you prefer manual setup:

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git pkg-config libsystemd-dev

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create required directories
sudo mkdir -p /var/lib/config-manager /var/log/config-manager
sudo groupadd -f config-manager
sudo usermod -a -G config-manager $USER
```

## Usage

### Configuration Manager

Apply configuration from YAML cookbooks:

```bash
# Apply all configurations in the cookbooks directory
python3 src/config_manager.py

# Apply configurations from a specific directory
python3 src/config_manager.py --config-dir /path/to/cookbooks

# Enable debug logging
python3 src/config_manager.py --debug
```

### Git Sync Service

Keep configuration cookbooks synchronized with a remote repository:

```bash
# Start continuous sync service (default 5-minute interval)
python3 src/sync_service.py

# Custom repository and settings
python3 src/sync_service.py \
    --repo-url https://github.com/your-repo/config-manager.git \
    --local-path /var/lib/config-manager/repo \
    --branch main \
    --interval 10

# Run sync once and exit
python3 src/sync_service.py --once
```

### Combined Workflow

For production use, typically you would:

1. **Start the sync service** to keep cookbooks updated:
   ```bash
   python3 src/sync_service.py &
   ```

2. **Run config manager periodically** via cron or systemd timer:
   ```bash
   # Add to crontab for hourly execution
   0 * * * * cd /path/to/config-manager && source .venv/bin/activate && python3 src/config_manager.py
   ```

## YAML Cookbook Format

Cookbooks are YAML files that define the desired system state. Here's the structure:

```yaml
name: "Configuration Name"
description: "Description of what this configuration does"
version: "1.0.0"

# Install packages
install:
  pre_install:
    - command: "/usr/bin/apt-get update"
      sudo: true
  install:
    - package: nginx
      version: latest
      state: present
  post_install:
    - command: "/bin/systemctl enable nginx"
      sudo: true

# Remove packages (optional)
remove:
  packages:
    - name: apache2

# Configure files and services
configure:
  files:
    - path: /etc/nginx/nginx.conf
      content: |
        # Nginx configuration content here
        user www-data;
        worker_processes auto;
      owner: root
      group: root
      mode: "0644"
  
  services:
    - name: nginx
      state: restarted
      enabled: true
```

### Cookbook Examples

See `cookbooks/webserver.yaml` for a complete example that:
- Installs NGINX and PHP-FPM
- Configures web server settings
- Creates test pages
- Manages service states

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

### Running Tests

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run tests with coverage
pytest --cov=src tests/
```

### Adding New Cookbooks

1. Create a new YAML file in the `cookbooks/` directory
2. Follow the cookbook format described above
3. Test with `python3 src/config_manager.py --config-dir cookbooks/`

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   - Ensure user is in the `config-manager` group
   - Log out and back in after running bootstrap script
   - Check `/var/lib/config-manager` permissions

2. **Git Sync Failures**
   - Verify repository URL and credentials
   - Check network connectivity
   - Ensure git is installed and configured

3. **Package Installation Failures**
   - Update package lists: `sudo apt-get update`
   - Check for conflicting packages
   - Review error logs in `/var/log/config-manager/`

### Logs

- Application logs: Use `--debug` flag for verbose output
- System logs: Check `/var/log/config-manager/` directory
- Service logs: `journalctl -u your-service-name`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request
