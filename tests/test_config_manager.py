"""Tests for config_manager module."""

import unittest
import sys
import os
import tempfile
from unittest.mock import patch, Mock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Tests for ConfigManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cookbook_path = os.path.join(self.temp_dir, 'test.yaml')
        
        # Create a simple test cookbook
        with open(self.cookbook_path, 'w') as f:
            f.write("""name: Test Config
packages:
  - git
  - vim
files:
  - source: test.txt
    destination: /tmp/test.txt
    mode: "0644"
services:
  - nginx
""")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test ConfigManager initialization."""
        manager = ConfigManager()
        self.assertIsInstance(manager.state, dict)
        self.assertIsInstance(manager.sudo, bool)

    @patch('config_manager.subprocess.run')
    def test_apply_config(self, mock_run):
        """Test applying configuration from YAML file."""
        mock_run.return_value.returncode = 0
        
        manager = ConfigManager()
        success, (checksum, rel_path) = manager.apply_config(self.cookbook_path)
        
        self.assertTrue(success)
        self.assertIsInstance(checksum, str)
        self.assertIsInstance(rel_path, str)

    @patch('config_manager.subprocess.run')
    def test_run_cmd(self, mock_run):
        """Test command execution."""
        mock_run.return_value.returncode = 0
        
        manager = ConfigManager()
        result = manager.run_cmd(['echo', 'test'])
        
        self.assertTrue(result)
        mock_run.assert_called()

    def test_check_file_state(self):
        """Test file state checking functionality."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, 'test.txt')
        test_content = 'test content'
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        manager = ConfigManager()
        result = manager.check_file_state(test_file, test_content)
        
        self.assertIsInstance(result, bool)

    @patch('config_manager.subprocess.run')
    def test_check_package_installed(self, mock_run):
        """Test package installation check."""
        # Mock successful package check with proper stdout
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'install ok installed'
        mock_run.return_value = mock_result
        
        manager = ConfigManager()
        result = manager.check_package_installed('git')
        
        self.assertTrue(result)
        mock_run.assert_called()

    def test_yaml_loading(self):
        """Test YAML configuration loading."""
        manager = ConfigManager()
        
        # Test loading YAML content directly
        import yaml
        with open(self.cookbook_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Basic validation - config should be a dict
        self.assertIsInstance(config, dict)
        self.assertIn('name', config)
        self.assertEqual(config['name'], 'Test Config')
        
        # Should have expected keys
        expected_keys = ['packages', 'files', 'services']
        for key in expected_keys:
            self.assertIn(key, config)


if __name__ == '__main__':
    unittest.main()
