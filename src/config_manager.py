"""Package and service configuration manager using YAML files."""
import os
import glob
import yaml
import click
import json
import hashlib
import logging
import subprocess
from typing import Optional, List, Tuple, Dict
from constants import (
    DEFAULT_LOCAL_PATH,
    LOG_FORMAT,
    LOG_LEVEL,
)

# Configure logging
# TDOO : Need to move logging module to a common place.
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)


# TODO : This need to move to constants file.
STATE_FILE = '/var/lib/config-manager/state.json'

class ConfigManager:
    """Configuration manager for packages, files, and services.
    TODO : If time permits, expand the docstring with usage examples and basic docstring test cases.
    """

    def __init__(self):
        self.sudo = os.geteuid() != 0
        self.state = self._load_state()

        
    def _load_state(self) -> Dict[str, str]:
        """Load state from state file to make it idempotent."""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            else:
                # TODO : This section can be improved at bootstrap time.
                # Initialize with empty state if file doesn't exist
                os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
                with open(STATE_FILE, 'w') as f:
                    json.dump({}, f)
            return {}
        except Exception as e:
            logger.warning(f"Failed to load state file: {e}")
            return {}
            
    def _save_state(self):
        """Save state to state file."""
        try:
            # TODO: Check if directory exists and create if not.keeping it simple for now.
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.info("State saved successfully")
        except Exception as e:
            logger.warening(f"Failed to save state file: {e}")
            
    def _get_config_checksum(self, config_file: str) -> str:
        """Calculate SHA256 checksum of config file."""
        with open(config_file, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
            
    def _config_changed(self, config_file: str) -> Tuple[bool, str]:
        """Check if yaml file has changed since last run.
        Returns (changed, checksum) tuple."""
        try:
            # Convert to relative path from the workspace root
            rel_path = os.path.relpath(config_file)
            current_checksum = self._get_config_checksum(config_file)
            last_checksum = self.state.get(rel_path)
            
            if current_checksum == last_checksum:
                logger.info(f"Config {rel_path} unchanged since last run, skipping")
                return False, current_checksum
                
            logger.info(f"Config {rel_path} has changed, will apply updates")
            return True, current_checksum
        except Exception as e:
            logger.warning(f"Failed to check config changes: {e}")
            return True  # Fallback : Apply config if we can't verify checksum

    def run_cmd(self, cmd: list) -> bool:
        """ Wraper to Run a command with sudo if needed.
        Returns True if command succeeded, False otherwise.
        Constraints: Spports only unix based systems with sudo installed.
        """
        try:
            if self.sudo:
                # TODO : This logic cab be improved.Keeping it basic for now.
                cmd.insert(0, 'sudo')
            logger.info(f"Running: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e.stderr}")
            return False

    def check_package_installed(self, package: str) -> bool:
        """Check if a package is installed.
        Returns True if installed, False otherwise."""
        try:
            result = subprocess.run(['dpkg-query', '-W', '-f=${Status}', package],
                                 check=True, capture_output=True, text=True)
            return 'install ok installed' in result.stdout
        except subprocess.CalledProcessError:
            logger.error(f"Package {package} to check installation failed")
            return False
    
    def check_file_state(self, path: str, content: str, mode: str = None,
                        owner: str = None, group: str = None) -> bool:
        """Check if a file's content and metadata match desired state."""
        try:
            # Doing basic checks for now. Can be expanded as needed.
            if not os.path.exists(path):
                return False
                
            # Check content
            with open(path, 'r') as f:
                if f.read() != content:
                    return False
                    
            # Check mode
            if mode and oct(os.stat(path).st_mode)[-3:] != mode:
                return False
                
            # Check ownership
            if owner or group:
                stat = os.stat(path)
                import pwd, grp
                current_owner = pwd.getpwuid(stat.st_uid).pw_name
                current_group = grp.getgrgid(stat.st_gid).gr_name
                if (owner and current_owner != owner) or (group and current_group != group):
                    return False
                    
            return True
        except Exception:
            logger.error(f"Failed to check file state for {path}")
            return False

    def apply_config(self, config_file: str) -> Tuple[bool, Tuple[str, str]]:
        """Apply configuration from YAML file.
        Returns: (success, (checksum, relative_path)) tuple.
        TODO : Need to do more brainstroming on YAML vs JSON and structure.
        """
        try:
            # Check if config has changed
            changed, checksum = self._config_changed(config_file)
            if not changed:
                return True, (checksum, os.path.relpath(config_file))
                
            with open(config_file,'r') as f:
                config = yaml.safe_load(f)
            
            if not config:
                logger.error(f"Empty or invalid config file: {config_file}")
                return False

            logger.info(f"Applying configuration from: {config_file}")

            ########## Actual application logic starts here ##########
            # Update package lists
            # TODO : This can be optimized to run only once if multiple configs are applied.
        
            # Remove packages
            # TODO : Remove section can be improved by doing diff from old file vs new file and auto
            # detecting removed packages. For now, keeping it simple.
            if 'remove' in config:
                for pkg in config['remove'].get('packages', []):
                    name = pkg.get('name')
                    if name and self.check_package_installed(name):
                        if not self.run_cmd(['/usr/bin/apt-get', 'remove', '-y', name]):
                            return False
            
            # Preinstall  packages
            # TODO : Need to put more checks in commands before proceeding.
            if 'install' in config:
                # Handle pre-installation steps
                for step in config['install'].get('pre_install', []):
                    if 'command' in step:
                        if not self.run_cmd(step['command'].split()):
                            logger.error(f"Pre-install command failed: {step['command']}")
                            return False

                # Install packages
                for pkg in config['install'].get('install', []):
                    name = pkg.get('package')
                    if name and not self.check_package_installed(name):
                        if not self.run_cmd(['/usr/bin/apt-get', 'install', '-y', name]):
                            logger.error(f"Installation of package {name} failed")
                            return False
                            
                # Handle post-installation steps
                for step in config['install'].get('post_install', []):
                    if 'command' in step:
                        if not self.run_cmd(step['command'].split()):
                            logger.error(f"Post-install command failed: {step['command']}")
                            return False

            # Configure files
            if 'configure' in config:
                for file_cfg in config['configure'].get('files', []):
                    path = file_cfg.get('path')
                    # Doing Basic yaml validation
                    if not path:
                        continue

                    content = file_cfg.get('content', '')
                    mode = file_cfg.get('mode')
                    owner = file_cfg.get('owner')
                    group = file_cfg.get('group')
                    
                    # Optimization-1: Only update if current state doesn't match desired state
                    current_state = self.check_file_state(path, content, mode, owner, group)
                    if not current_state:
                        logger.info(f"Updating file {path} due to state mismatch")
                        
                        # Create directory with sudo if needed
                        dirname = os.path.dirname(path)
                        try:
                            if not os.path.exists(dirname):
                                if not self.run_cmd(['mkdir', '-p', dirname]):
                                    logger.error(f"Failed to create directory for {path}")
                                    return False
                        except Exception as e:
                            logger.error(f"Failed to create directory for {path}: {e}")
                            # Can be raise or contibue based on use-case
                            return False
                        
                        # Write content through sudo
                        # Using a temp file to ensure atomic write, permission harness, and backup.
                        
                        temp_path = f"/tmp/{os.path.basename(path)}.tmp"
                        try:
                            with open(temp_path, 'w') as f:
                                f.write(content)
                        except Exception as e:
                            logger.error(f"Failed to write content to temp file for {path}: {e}")
                            return False
                        
                        # Move file to destination with sudo
                        try:
                            if not self.run_cmd(['mv', temp_path, path]):
                                # optimization-2: Clean up temp file if move failed
                                if os.path.exists(temp_path):
                                    os.unlink(temp_path)
                                logger.error(f"Failed to move temp file to {path}")
                                return False
                        except Exception as e:
                            logger.error(f"Failed to move temp file to {path}: {e}")
                            return False
                            
                        logger.info(f"Updated content of {path}")

                        # Set ownership first
                        if owner or group:
                            ownership = f"{owner or 'root'}:{group or 'root'}"
                            logger.info(f"Setting ownership {ownership} on {path}")
                            try:
                                if not self.run_cmd(['chown', ownership, path]):
                                    logger.error(f"Failed to set ownership for {path}")
                                    return False
                            except Exception as e:
                                logger.error(f"Failed to set ownership for {path}: {e}")
                                return False
                        
                        # Then set mode
                        if mode:
                            logger.info(f"Setting mode {mode} on {path}")
                            try:
                                if not self.run_cmd(['chmod', mode, path]):
                                    logger.error(f"Failed to set mode for {path}")
                                    return False
                            except Exception as e:
                                logger.error(f"Failed to set mode for {path}: {e}")
                                return False
                    else:
                        logger.info(f"File {path} already in desired state")
                        return False

            # Configure services
            if 'configure' in config:
                for svc in config['configure'].get('services', []):
                    name = svc.get('name')
                    if not name:
                        continue

                    # Handle service state
                    # TODO : Need to move state mapping to constants file.
                    state_map = {
                        'started': 'start',
                        'stopped': 'stop',
                        'restarted': 'restart'
                    }
                    
                    if (state := svc.get('state')) in state_map:
                        if not self.run_cmd(['systemctl', state_map[state], name]):
                            return False

                    enabled = svc.get('enabled')
                    if enabled is not None:
                        cmd = 'enable' if enabled else 'disable'
                        if not self.run_cmd(['systemctl', cmd, name]):
                            return False

            logger.info("Configuration applied successfully")
            return True, (checksum, os.path.relpath(config_file))
        except Exception as e:
            logger.error(f"Failed to apply config: {e}")
            return False, (None, os.path.relpath(config_file))

def process_configs(config_dir: str) -> List[Tuple[str, bool, Optional[str]]]:
    """Process all configs in the given directory."""
    results = []
    manager = ConfigManager()
    pending_state_updates = {}
    
    config_files = glob.glob(os.path.join(config_dir, '*.yaml'))
    for config_file in config_files:
        name = os.path.basename(config_file)
        try:
            success, new_state = manager.apply_config(config_file)
            if success:
                # Store successful state changes to apply later
                pending_state_updates[os.path.relpath(config_file)] = new_state[0]
            results.append((name, success, None))
        except Exception as e:
            results.append((name, False, str(e)))
    
    # Only update state file if all configs were successful
    if all(result[1] for result in results):
        try:
            # Update state with all successful changes
            manager.state.update(pending_state_updates)
            manager._save_state()
            logger.info("All configurations successful - state file updated")
        except Exception as e:
            logger.error(f"Failed to save final state: {e}")
            # Mark all results as failed if we couldn't save state
            results = [(name, False, "Failed to save state") for name, _, _ in results]
    else:
        logger.warning("Some configurations failed - state not updated")
            
    return results

@click.command()
@click.option(
    '--config-dir', '-c',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),

    default= os.path.join(DEFAULT_LOCAL_PATH, 'cookbooks'),
    help=f'Directory containing YAML configuration files (default: {DEFAULT_LOCAL_PATH}/cookbooks)',
    show_default=True
)
@click.option('--debug', '-d', is_flag=True, help='Enable debug logging')

def main(config_dir: str, debug: bool) -> None:
    """Package and configuration manager using YAML files.
    Main method is just for user friedenly status update.
    
    Processes all YAML configuration files in the specified CONFIG_DIR and applies their
    configurations to the system. Each config can specify:

    - Package installations
    - File configurations with content and permissions
    - Service configurations (state and enabled status)
    """
    config_files = glob.glob(os.path.join(config_dir, '*.yaml'))
    if not config_files:
        click.echo(f"ERROR: No config files found in: {config_dir}", err=True)
        raise click.Abort()

    click.echo(f"INFO: Found {len(config_files)} config file(s)")
    
    try:
        results = process_configs(config_dir)
        
        # Print summary
        total = len(results)
        succeeded = sum(1 for r in results if r[1])
        click.echo(f"\nProcessed {total} configs: {succeeded} succeeded, {total - succeeded} failed")
        
        for name, success, error in results:
            status = "[OK]" if success else "[FAILED]"
            msg = error if error else ("Success" if success else "Failed")
            click.echo(f"{status} {name}: {msg}")
            
        if succeeded != total:
            raise click.Abort()
            
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"\nERROR: {str(e)}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    main()
