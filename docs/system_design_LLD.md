# Config Manager - Low Level Design Document
Original quip link for reference : https://quip.com/APjeAWDFqIvB/Config-Manager-Low-Level-Design-Document

## Document Information

| **Field** | **Value** |
|-----------|-----------|
| **Document Title** | Config Manager - Low Level Design |
| **Version** | 1.0 |
| **Author** | Development Team |
| **Date** | October 6, 2025 |
| **Status** | Draft |

## Table of Contents

1. [Introduction](#introduction)
2. [Module Design](#module-design)
3. [Class Diagrams](#class-diagrams)
4. [Database Design](#database-design)
5. [API Specifications](#api-specifications)
6. [Algorithm Design](#algorithm-design)
7. [Error Handling](#error-handling)
8. [Security Implementation](#security-implementation)
9. [Performance Optimizations](#performance-optimizations)
10. [Testing Strategy](#testing-strategy)

## Introduction

This Low Level Design document provides detailed implementation specifications for the Config Manager system. It covers the internal structure of modules, classes, methods, data structures, and algorithms that implement the requirements specified in the High Level Design.

### Design Principles

- **Single Responsibility**: Each class has one clear purpose
- **Idempotency**: Operations can be safely repeated
- **Fail-Safe**: System defaults to safe state on errors
- **Modularity**: Loosely coupled, highly cohesive components
- **Testability**: All components are unit testable

## Module Design

### 1. Config Manager Module (`config_manager.py`)

#### Class: `ConfigManager`

**Purpose**: Core configuration application engine responsible for parsing YAML cookbooks and applying system changes.

```python
class ConfigManager:
    """Configuration manager for packages, files, and services."""
    
    def __init__(self) -> None
    def _load_state(self) -> Dict[str, str]
    def _save_state(self) -> None
    def _calculate_file_hash(self, content: str) -> str
    def apply_config(self, config_file: str) -> Tuple[bool, Tuple[str, str]]
    def check_package_installed(self, package: str) -> bool
    def check_file_state(self, path: str, content: str) -> bool
    def run_cmd(self, cmd: List[str]) -> bool
    def _install_packages(self, packages: List[Dict]) -> Tuple[bool, str]
    def _configure_files(self, files: List[Dict]) -> Tuple[bool, str]
    def _manage_services(self, services: List[Dict]) -> Tuple[bool, str]
    def _run_commands(self, commands: List[Dict]) -> Tuple[bool, str]
```

#### Attributes

| **Attribute** | **Type** | **Description** |
|---------------|----------|-----------------|
| `sudo` | `bool` | Whether sudo privileges are available |
| `state` | `Dict[str, str]` | Current system state cache |

#### Key Methods

##### `apply_config(config_file: str) -> Tuple[bool, Tuple[str, str]]`

**Purpose**: Parse and apply configuration from YAML cookbook file.

**Algorithm**:
```
1. Load and validate YAML configuration
2. Extract sections: install, configure, services
3. Apply configurations in order:
   a. Pre-install commands
   b. Package installations
   c. File configurations
   d. Service management
   e. Post-install commands
4. Update state tracking
5. Return success status and messages
```

**Error Handling**:
- YAML parsing errors → Return False with error message
- Missing required fields → Skip with warning
- Command execution failures → Rollback and return False

##### `check_package_installed(package: str) -> bool`

**Purpose**: Verify if a Debian package is installed on the system.

**Implementation**:
```python
def check_package_installed(self, package: str) -> bool:
    try:
        result = subprocess.run(
            ['dpkg', '-l', package],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False
```

##### `_calculate_file_hash(content: str) -> str`

**Purpose**: Generate SHA-256 hash for content comparison and state tracking.

**Implementation**:
```python
def _calculate_file_hash(self, content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()
```

#### State Management

**State File Location**: `/var/lib/config-manager/state.json`

**State Structure**:
```json
{
    "files": {
        "/etc/nginx/nginx.conf": "sha256_hash_value",
        "/var/www/html/index.php": "sha256_hash_value"
    },
    "packages": {
        "nginx": "1.18.0-0ubuntu1.4",
        "php7.4-fpm": "7.4.3-4ubuntu2.18"
    },
    "services": {
        "nginx": "active",
        "php7.4-fpm": "active"
    },
    "last_config_applied": "2025-10-06T10:30:00Z",
    "config_hash": "cookbook_hash_value"
}
```

### 2. Sync Service Module (`sync_service.py`)

#### Class: `SyncService`

**Purpose**: Git repository synchronization service for maintaining up-to-date configuration cookbooks.

```python
class SyncService:
    """Service that keeps a local git repository in sync with its remote."""
    
    def __init__(self, repo_url: str, local_path: str, branch: str, sync_interval: int) -> None
    def initialize_git_repo(self) -> bool
    def sync_git_repo(self) -> bool
    def start(self, once: bool = False) -> None
    def _is_repo_valid(self) -> bool
    def _handle_sync_conflict(self) -> bool
    def _staggered_delay(self) -> None
```

#### Attributes

| **Attribute** | **Type** | **Description** |
|---------------|----------|-----------------|
| `repo_url` | `str` | Git repository URL |
| `local_path` | `str` | Local repository path |
| `branch` | `str` | Git branch to sync |
| `sync_interval` | `int` | Polling interval in minutes |
| `repo` | `git.Repo` | GitPython repository object |

#### Key Methods

##### `initialize_git_repo() -> bool`

**Purpose**: Initialize local Git repository, clone if needed.

**Algorithm**:
```
1. Check if local path exists and is valid Git repo
2. If not exists:
   a. Create directory structure
   b. Clone remote repository
   c. Checkout specified branch
3. If exists but invalid:
   a. Backup existing content
   b. Re-clone repository
4. Verify repository integrity
5. Return initialization status
```

##### `sync_git_repo() -> bool`

**Purpose**: Synchronize local repository with remote changes.

**Algorithm**:
```
1. Fetch latest changes from remote
2. Check for conflicts
3. If no conflicts:
   a. Pull changes using fast-forward merge
   b. Update local branch
4. If conflicts detected:
   a. Log conflict details
   b. Reset to remote HEAD (force sync)
   c. Alert administrators
5. Verify sync integrity
6. Return sync status
```

**Conflict Resolution Strategy**:
- **Local Changes**: Force reset to remote (local changes discarded)
- **Merge Conflicts**: Reset to remote HEAD with backup
- **Network Issues**: Retry with exponential backoff

##### `_staggered_delay() -> None`

**Purpose**: Implement random delay to prevent thundering herd problem.

**Implementation**:
```python
import random
import time

def _staggered_delay(self) -> None:
    # Random delay between 0-60 seconds to stagger node sync
    delay = random.uniform(0, 60)
    time.sleep(delay)
```

### 3. Constants Module (`constants.py`)

#### Configuration Constants

```python
# Git Configuration
DEFAULT_REPO_URL: str = "https://github.com/susantomahato/config-manager.git"
DEFAULT_LOCAL_PATH: str = "/var/lib/config-manager/default_repo"
DEFAULT_BRANCH: str = "main"
DEFAULT_SYNC_INTERVAL: int = 5  # minutes

# System Paths
STATE_FILE: str = "/var/lib/config-manager/state.json"
LOG_FILE: str = "/var/log/config-manager/config-manager.log"
BACKUP_DIR: str = "/var/lib/config-manager/backups"

# Logging Configuration
LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(message)s"
LOG_LEVEL: str = "INFO"

# Performance Tuning
MAX_RETRY_ATTEMPTS: int = 3
RETRY_DELAY: int = 5  # seconds
COMMAND_TIMEOUT: int = 300  # seconds
MAX_LOG_SIZE: int = 10 * 1024 * 1024  # 10MB
```

## Class Diagrams

### Core Class Relationships

```
┌─────────────────────────────────────┐
│            ConfigManager            │
├─────────────────────────────────────┤
│ - sudo: bool                        │
│ - state: Dict[str, str]             │
├─────────────────────────────────────┤
│ + apply_config(file: str)           │
│ + check_package_installed(pkg: str) │
│ + check_file_state(path, content)   │
│ + run_cmd(cmd: List[str])           │
│ - _load_state()                     │
│ - _save_state()                     │
│ - _calculate_file_hash(content)     │
└─────────────────────────────────────┘
                    │
                    │ uses
                    ▼
┌─────────────────────────────────────┐
│            SyncService              │
├─────────────────────────────────────┤
│ - repo_url: str                     │
│ - local_path: str                   │
│ - branch: str                       │
│ - sync_interval: int                │
│ - repo: git.Repo                    │
├─────────────────────────────────────┤
│ + initialize_git_repo()             │
│ + sync_git_repo()                   │
│ + start(once: bool)                 │
│ - _is_repo_valid()                  │
│ - _handle_sync_conflict()           │
└─────────────────────────────────────┘
```

### CLI Interface Classes

```
┌─────────────────────────────────────┐
│               CLI                   │
├─────────────────────────────────────┤
│ @click.group()                      │
│ + config()                          │
│ + sync()                            │
│ + apply(config_file: str)           │
│ + status()                          │
└─────────────────────────────────────┘
                    │
                    │ instantiates
                    ▼
┌─────────────────────────────────────┐
│          ConfigManager              │
│            SyncService              │
└─────────────────────────────────────┘
```

## Database Design

### State File Schema (`state.json`)

The system uses a JSON-based state file for persistence. This lightweight approach avoids database dependencies while providing necessary state tracking.

#### Schema Definition

```json
{
  "file_path":"content checksum"
}
```

#### Data Access Patterns -- Pending

1. **Read State**: Load entire state file into memory at startup
2. **Write State**: Atomic write with temporary file and move operation
3. **State Comparison**: Compare hashes to detect configuration drift
4. **Backup Strategy**: Rotate state files with timestamps

#### Performance Considerations -- Pending

- **File Size**: Typical state file <1MB for 100 files/packages
- **Read Performance**: Single file read operation, <10ms
- **Write Performance**: Atomic writes prevent corruption
- **Concurrency**: File locking prevents concurrent modifications

## API Specifications

### Command Line Interface

#### `config-manager `

**Purpose**: Apply configuration from YAML cookbook file.

```bash
config-manager  [OPTIONS] CONFIG_FILE

Options:
  --verbose    Enable verbose output
  --help       Show help message
```

**Return Codes**:
- `0`: Success
- `1`: Configuration errors
- `2`: Permission errors
- `3`: System errors

#### `config-manager sync`

**Purpose**: Synchronize with Git repository.

```bash
config-manager sync [OPTIONS]

Options:
  --once       Sync once and exit (no daemon mode)
  --interval   Sync interval in minutes (default: 5)
  --repo-url   Git repository URL
  --branch     Git branch to sync (default: main)
  --help       Show help message
```

#### `config-manager status`

**Purpose**: Show current system status and configuration state.

```bash
config-manager status [OPTIONS]

Options:
  --format     Output format: table, json, yaml (default: table)
  --verbose    Show detailed status information
  --help       Show help message
```


#### Idempotency Implementation

**Hash-based Change Detection**:

```python
def is_change_required(resource_type: str, resource_id: str, new_content: str) -> bool:
    """
    Determine if a change is required using hash comparison.
    """
    current_hash = self.state.get(f"{resource_type}.{resource_id}")
    new_hash = hashlib.sha256(new_content.encode()).hexdigest()
    
    return current_hash != new_hash
```

**State Update Pattern**:

```python
def update_state_atomically(updates: Dict[str, str]):
    """
    Atomically update state file with new hash values.
    """
    # Read current state
    current_state = load_state()
    
    # Apply updates
    current_state.update(updates)
    
    # Atomic write with temporary file
    temp_file = STATE_FILE + '.tmp'
    with open(temp_file, 'w') as f:
        json.dump(current_state, f, indent=2)
    
    # Atomic move
    os.rename(temp_file, STATE_FILE)
```

### Logging Strategy

#### Log Levels and Categories

```python
# Critical system errors that require immediate attention
logger.critical("State file corrupted, manual intervention required")

# Errors that prevent operation but system can continue
logger.error("Failed to apply configuration: %s", error_msg)

# Warning conditions that should be monitored
logger.warning("Git sync conflicts detected, forcing reset")

# Information about normal operation
logger.info("Configuration applied successfully: %s", config_file)

# Detailed information for debugging
logger.debug("Package check result: %s -> %s", package, installed)
```

