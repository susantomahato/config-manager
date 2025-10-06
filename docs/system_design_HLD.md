# Config Manager - System Design Document

## Executive Summary

Config Manager is a lightweight, Python-based configuration management system designed to automate server provisioning and maintain consistent system states across multiple nodes. The system uses YAML-based cookbooks for configuration specification and Git for distributed configuration synchronization.

## Problem Statement

Traditional configuration management requires building a tool that can:
- Configure multiple servers for production PHP web applications
- Provide abstractions for file management, package installation, and service control
- Maintain idempotent operations without using existing tools (Puppet, Chef, Ansible)
- Deliver reliable, scalable configuration deployment

## System Requirements

### Functional Requirements

| Requirement | Description | Implementation |
|-------------|-------------|----------------|
| **FR-001** | Bootstrap dependency resolution | `bootstrap.sh` script for Ubuntu setup |
| **FR-002** | File content and metadata management | YAML-based file specifications with owner, group, mode |
| **FR-003** | Debian package management | Install/remove packages via apt |
| **FR-004** | Service lifecycle management | Restart services on configuration changes |
| **FR-005** | Web server deployment | NGINX + PHP-FPM configuration for "Hello, world!" |

### Non-Functional Requirements

| Requirement | Description | Implementation |
|-------------|-------------|----------------|
| **NFR-001** | Idempotent operations | State tracking with checksums, safe re-execution |
| **NFR-002** | Documentation coverage | Architecture, installation, configuration guides |
| **NFR-003** | High availability | No server reboots, rolling updates |
| **NFR-004** | Scalability | Git-based distribution, independent node operation |

## System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Git Remote    │    │  Sync Service   │    │  Config Manager  │    │   Target Node   │
│   Repository    │◄───┤   (Pull Mode)   │──► │      Core        │──► │   (Server)      │
└─────────────────┘    └─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │                        │                        │
        │                        │                        │                        │
        ▼                        ▼                        ▼                        ▼
┌─────────────┐          ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
│ Cookbooks   │          │ Local Git   │          │ YAML Parser │          │ Packages    │
│ (YAML)      │          │ Repository  │          │ & Validator │          │ Files       │
└─────────────┘          └─────────────┘          └─────────────┘          │ Services    │
                                                                           └─────────────┘
```

**Component Interaction Flow:**
1. **Sync Service** polls Git Remote Repository for configuration updates
2. **Local Git Repository** stores the latest cookbook configurations
3. **Config Manager Core** reads and parses YAML cookbooks
4. **System Changes** applied to target node (packages, files, services)

### Component Architecture

#### Core Components

1. **Config Manager** (`src/config_manager.py`)
   - Primary configuration application engine
   - YAML parsing and validation
   - Package, file, and service management
   - State tracking and idempotency

2. **Sync Service** (`src/sync_service.py`)
   - Git repository synchronization
   - Periodic polling for configuration updates
   - Branch management and conflict resolution

3. **Constants Module** (`src/constants.py`)
   - Configuration parameters and defaults
   - Logging configuration
   - System paths and settings

#### Data Flow

```
Git Repository → Sync Service → Local Repository → Config Manager → System Changes
      │              │              │                │              │
      │              ▼              │                ▼              ▼
   Remote Updates  Pull/Clone   YAML Cookbooks   Parse & Apply   Packages
   Configuration   Operations      Validation     Configuration   Services
   Changes                         State Check                     Files
```

**Detailed Flow:**
1. **Configuration Updates**: New cookbooks pushed to Git repository
2. **Sync Operation**: Periodic pull operations by Sync Service
3. **Local Storage**: Cookbooks stored in local Git repository
4. **Processing**: Config Manager validates and applies configurations
5. **System State**: Target node updated with new configuration state

## Deployment Patterns

### Pull-Based Model (Implemented)

**Advantages:**
- **Scalability**: Nodes operate independently, reducing central server load
- **Fault Tolerance**: Continues operation if central repository is temporarily unavailable
- **Self-Healing**: Automatic drift detection and correction
- **Distributed Load**: Git clone/pull operations distributed across nodes

**Disadvantages:**
- **Latency**: Configuration changes only applied during polling intervals
- **Coordination Complexity**: Harder to orchestrate fleet-wide updates
- **Resource Usage**: Each node maintains full repository copy

### Alternative: Push-Based Model (Not Implemented)

**Advantages:**
- **Real-time Updates**: Immediate configuration propagation
- **Central Control**: Operator-driven deployment timing
- **Targeted Updates**: Selective node configuration

**Disadvantages:**
- **Scalability Limits**: Central server bottleneck for large fleets
- **Network Dependencies**: Requires persistent connectivity
- **Single Point of Failure**: Central controller availability critical

## Detailed Module Design

### Module 1: Git Synchronization Service

**Purpose**: Maintain up-to-date configuration cookbooks from remote repository

**Key Functions:**
```python
class SyncService:
    def initialize_git_repo() -> None
    def sync_git_repo() -> bool
    def start(once: bool = False) -> None
```

**Risk Mitigation:**
- Staggered polling intervals to prevent thundering herd
- Branch locking during sync operations
- Rollback capability on sync failures

### Module 2: Configuration Manager

**Purpose**: Apply YAML cookbook configurations to system state

**Key Functions:**
```python
class ConfigManager:
    def apply_config(config_file: str) -> Tuple[bool, Tuple[str, str]]
    def check_package_installed(package: str) -> bool
    def check_file_state(path: str, content: str) -> bool
    def run_cmd(cmd: list) -> bool
```

**State Management:**
- Checksum-based change detection
- Incremental updates only
- Configuration rollback support

### Module 3: Monitoring and Observability )(Pending)

**Purpose**: Comprehensive system monitoring, alerting, and automatic error recovery

**Key Functions:**
```python
class MonitoringService:
    def collect_metrics() -> Dict[str, Any]
    def detect_configuration_drift() -> List[str]
    def health_check() -> bool
    def trigger_rollback(error_context: str) -> bool
    def send_alerts(alert_type: str, message: str) -> None
```

**Metrics Collected:**
- **Performance Metrics**:
  - Configuration application success/failure rates
  - Sync operation timing and frequency
  - System resource utilization during operations
  - Service restart frequencies and duration
- **Health Metrics**:
  - Configuration drift detection
  - Service availability and response times
  - System resource consumption
  - Git repository connectivity status
- **Security Metrics**:
  - Failed authentication attempts
  - Unauthorized configuration changes
  - Permission violation attempts

**Auto-Rollback Mechanisms:**
- **Error Detection Triggers**:
  - Service startup failures after configuration changes
  - Critical system resource exhaustion
  - Configuration validation failures
  - Network connectivity issues
- **Rollback Process**:
  1. Immediate service restoration to last known good state
  2. Revert file system changes using state snapshots
  3. Package downgrade to previous versions if necessary
  4. Alert administrators with detailed error context
  5. Quarantine problematic configurations for review

**Alerting and Notifications:**
- Real-time notifications via email, Slack, or webhook
- Escalation policies for critical failures
- Automated incident creation in ticketing systems
- Performance degradation warnings

## YAML Cookbook Specification

### Structure
```yaml
name: "Configuration Name"
version: "1.0.0"
description: "Configuration description"

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

configure:
  files:
    - path: /etc/nginx/nginx.conf
      content: |
        # Configuration content
      owner: root
      group: root
      mode: "0644"
  
  services:
    - name: nginx
      state: started
      enabled: true
```

## Security Considerations

### Access Control
- Git repository access via SSH keys or HTTPS tokens
- Sudo privilege management for system operations
- File permission validation and enforcement

### Data Protection
- Configuration state file protection (`/var/lib/config-manager/state.json`)
- Secure handling of sensitive configuration data
- Audit logging for all system modifications

## Performance Characteristics

### Scalability Metrics
- **Node Capacity**: 1000+ nodes per Git repository
- **Sync Frequency**: 5-minute default intervals, configurable
- **Configuration Size**: Up to 100MB cookbook repositories
- **Application Time**: <30 seconds for typical web server setup

### Resource Requirements
- **Memory**: 50MB baseline, 100MB during large configurations
- **Disk**: 500MB for tool + cookbooks, /var/lib storage
- **Network**: Minimal bandwidth, burst during Git operations
- **CPU**: Low baseline, spikes during package installations

## Business Impact

### Key Performance Indicators (KPIs)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Deployment Success Rate** | >99.5% | Successful config applications / Total attempts |
| **Mean Time to Deployment** | <10 minutes | Time from Git commit to node application |
| **Configuration Drift Detection** | <5 minutes | Time to detect and correct drift |
| **System Uptime** | >99.9% | Service availability during configuration updates |
| **Mean Time to Recovery (MTTR)** | <2 minutes | Time from error detection to service restoration |
| **Auto-Rollback Success Rate** | >98% | Successful automated rollbacks / Total rollback attempts |
| **False Positive Rate** | <2% | Unnecessary rollbacks / Total rollback triggers |
| **Monitoring Data Retention** | 30 days | Historical metrics and audit trail storage |

### Business Value
- **Revenue Protection**: Reduced service outages through automated consistency
- **Risk Reduction**: Automated compliance and security configuration
- **Cost Optimization**: Reduced manual operations overhead
- **Innovation Acceleration**: Faster deployment cycles and rollback capability

## Auto-Rollback Architecture

### Rollback Strategy

**State Snapshot Management:**
```python
class StateManager:
    def create_snapshot(self, config_name: str) -> str
    def restore_snapshot(self, snapshot_id: str) -> bool
    def validate_system_health(self) -> Tuple[bool, List[str]]
    def emergency_rollback(self, reason: str) -> bool
```

**Multi-Level Rollback Approach:**

1. **Application-Level Rollback** (Fastest - <30 seconds)
   - Revert service configurations
   - Restore application files
   - Restart affected services

2. **System-Level Rollback** (Medium - 1-2 minutes)
   - Package version downgrades
   - System configuration restoration
   - Dependency resolution

3. **Full System Restoration** (Slowest - 5-10 minutes)
   - Complete system state restoration
   - Full service stack restart
   - Comprehensive health validation


## Implementation Timeline

### Phase 1: Core Development (Completed)
- Basic configuration management functionality
- YAML cookbook parsing and application
- Package and service management
- State tracking and idempotency

### Phase 2: Git Integration (Completed)
- Repository synchronization service
- Continuous polling mechanism
- Conflict resolution and error handling

### Phase 3: Production Hardening (Completed)
- Comprehensive error handling and logging
- State management and recovery
- Testing framework and validation

### Phase 4: Advanced Features (Future)
- Web-based configuration dashboard
- Multi-environment configuration management
- Integration with CI/CD pipelines
- Configuration templating and variables

### Phase 5: Monitoring and Observability (Future)
- Real-time metrics collection and dashboards
- Configuration drift monitoring and alerting
- Performance analytics and optimization recommendations
- Audit trail and compliance reporting
- Health checks and system diagnostics
- Integration with monitoring systems (Prometheus, Grafana)
- Automated rollback mechanisms on error detection

## Comparison with Existing Solutions

| Feature | Config Manager | Puppet | Chef | Ansible |
|---------|---------------|---------|------|---------|
| **Language** | Python | Ruby + DSL | Ruby | Python |
| **Architecture** | Pull-based | Pull-based | Pull-based | Push-based |
| **Configuration** | YAML | Puppet DSL | Ruby DSL | YAML |
| **Dependencies** | Minimal | Ruby runtime | Ruby runtime | SSH access |
| **Learning Curve** | Low | Medium | High | Low |
| **Scalability** | Medium | High | High | Medium |

## Conclusion

Config Manager provides a lightweight, effective solution for configuration management with a focus on simplicity and reliability. The pull-based architecture ensures scalability while maintaining operational simplicity, making it suitable for small to medium-scale deployments requiring automated configuration management without the complexity of enterprise solutions.
