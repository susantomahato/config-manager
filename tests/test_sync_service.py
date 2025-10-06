"""Tests for sync_service module."""

import unittest
import sys
import os
from unittest.mock import patch, Mock, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sync_service import SyncService


class TestSyncService(unittest.TestCase):
    """Tests for SyncService class."""

    def setUp(self):
        """Set up test fixtures."""
        self.repo_url = "https://github.com/test/test-repo.git"
        self.local_path = "/tmp/test-repo"

    @patch.object(SyncService, 'initialize_git_repo')
    def test_init(self, mock_init_repo):
        """Test SyncService initialization."""
        service = SyncService(self.repo_url, self.local_path)
        self.assertEqual(service.repo_url, self.repo_url)
        self.assertEqual(service.local_path, os.path.abspath(self.local_path))
        mock_init_repo.assert_called_once()

    @patch('sync_service.git.Repo.clone_from')
    @patch('sync_service.os.path.exists')
    def test_initialize_git_repo_clone(self, mock_exists, mock_clone):
        """Test repository cloning when directory doesn't exist."""
        mock_exists.return_value = False  # Directory doesn't exist
        mock_repo = Mock()
        mock_clone.return_value = mock_repo
        
        with patch.object(SyncService, 'initialize_git_repo', wraps=SyncService.initialize_git_repo):
            service = SyncService.__new__(SyncService)
            service.repo_url = self.repo_url
            service.local_path = os.path.abspath(self.local_path)
            service.branch = "main"
            
            # Call the real method
            SyncService.initialize_git_repo(service)
            
            mock_clone.assert_called_once_with(self.repo_url, service.local_path)

    @patch.object(SyncService, 'initialize_git_repo')
    def test_sync_git_repo(self, mock_init_repo):
        """Test syncing repository."""
        # Create properly mocked repo with all required attributes
        mock_repo = MagicMock()
        mock_remote = Mock()
        mock_remote_commit = Mock()
        mock_local_commit = Mock()
        
        # Setup different commits to trigger pull
        mock_remote_commit.hexsha = "remote123"
        mock_local_commit.hexsha = "local456"
        
        # Setup mock structure
        mock_repo.remotes.origin = mock_remote
        mock_repo.refs = {"origin/main": Mock(commit=mock_remote_commit)}
        mock_repo.heads = {"main": Mock(commit=mock_local_commit)}
        mock_repo.git.pull = Mock()
        
        service = SyncService(self.repo_url, self.local_path)
        service.repo = mock_repo
        service.branch = "main"
        
        result = service.sync_git_repo()
        
        self.assertTrue(result)
        mock_remote.fetch.assert_called_once()
        mock_repo.git.pull.assert_called_once_with("origin", "main")

    @patch.object(SyncService, 'initialize_git_repo')
    def test_sync_git_repo_no_updates(self, mock_init_repo):
        """Test sync when no updates are available."""
        # Create properly mocked repo
        mock_repo = MagicMock()
        mock_remote = Mock()
        mock_commit = Mock()
        
        # Setup same commit locally and remotely (no updates)
        mock_commit.hexsha = "same123"
        
        mock_repo.remotes.origin = mock_remote
        mock_repo.refs = {"origin/main": Mock(commit=mock_commit)}
        mock_repo.heads = {"main": Mock(commit=mock_commit)}
        mock_repo.git.pull = Mock()
        
        service = SyncService(self.repo_url, self.local_path)
        service.repo = mock_repo
        service.branch = "main"
        
        result = service.sync_git_repo()
        
        self.assertFalse(result)  # Should return False when no updates
        mock_remote.fetch.assert_called_once()
        mock_repo.git.pull.assert_not_called()  # Should not pull when no updates


if __name__ == '__main__':
    unittest.main()