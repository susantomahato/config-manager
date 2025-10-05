import os

# Git Configuration Constants
DEFAULT_REPO_URL = "https://github.com/susantomahato/config-manager.git"
DEFAULT_LOCAL_PATH = os.path.expanduser("/var/lib/config-manager/default_repo")
DEFAULT_BRANCH = "main"
DEFAULT_SYNC_INTERVAL = 5  # minutes

# Logging Constants
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

