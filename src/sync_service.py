"""Git repository sync service - keeps local repo in sync with remote."""

import os
import time
import git
import logging
import click
from constants import (
    DEFAULT_REPO_URL,
    DEFAULT_LOCAL_PATH,
    DEFAULT_BRANCH,
    DEFAULT_SYNC_INTERVAL,
    LOG_FORMAT,
    LOG_LEVEL,
)

# Configure logging
# TDOO : Need to move logging module to a common place.
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class SyncService:
    """Service that keeps a local git repository in sync with its remote.
    TODO : 
        1. Add more details here, e.g., how it works, what it does on changes, etc.
        2. Put some basic docsrting tests bu that might increase the file size a bit.Need more brainstroming.
        3. Auto rollback to previous commit if any error occurs in core functionalities.
        4. Centralized error handling and logging mechanism for auto rollback.
        5. Add unit tests.
        6. Constraint : Need to  check do git have any limit and throthling  when constant hit(5 minute) from multiple nodes?
        7. At any point of time only one instance of this service should be running.
        
    Risks :
        1. Can bring entire application  offline if sync/ applly duration is same on all node with restart.
        2. If multiple nodes are syncing at the same time, can create a throtling issue with git repo.
        3. Partitial load/ write of cookbook can leave system in inconsistent state.
        ....Keep Adding risks as we go along.
    """

    def __init__(
        self,
        repo_url: str = DEFAULT_REPO_URL,
        local_path: str = DEFAULT_LOCAL_PATH,
        branch: str = DEFAULT_BRANCH,
        sync_interval: int = 5,
    ):  # Default 5 minutes
        """Initialize the sync service."""
        self.repo_url: str = repo_url
        self.local_path: str = os.path.abspath(local_path)
        self.branch: str = branch
        self.sync_interval: int = sync_interval

        # Initialize repository
        self.initialize_git_repo()

    def initialize_git_repo(self) -> None:
        """Initialize or open the git repository.
        TODO : Can happen file permmission issue.Will check it later.For now handling it with bootstrap.sh.
        """
        try:
            if not os.path.exists(os.path.join(self.local_path, ".git")):
                logger.info(f"Cloning repository from {self.repo_url}")
                self.repo = git.Repo.clone_from(self.repo_url, self.local_path)
            else:
                logger.info("Using existing repository")
                self.repo = git.Repo(self.local_path)

            # Set the remote branch to track
            self.repo.git.checkout(self.branch)
        except Exception as e:
            error_msg = f"Failed to initialize repository: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def sync_git_repo(self) -> bool:
        """Sync the local repository with remote, with defined intervial."""
        try:
            logger.info("Checking for repository updates")

            # Fetch updates from remote
            self.repo.remotes.origin.fetch()

            # Get the latest commit on the remote branch
            remote_commit = self.repo.refs[f"origin/{self.branch}"].commit
            local_commit = self.repo.heads[self.branch].commit

            if remote_commit.hexsha != local_commit.hexsha:
                logger.info("Changes detected in remote repository")
                self.repo.git.pull("origin", self.branch)
                logger.info("Successfully pulled changes")
                return True
            else:
                logger.info("Repository is up to date")
                return False

        except Exception as e:
            logger.error(f"Error syncing repository: {str(e)}")
            raise

    def start(self, once: bool = False) -> None:
        """Start the sync service."""
        try:
            logger.info(f"Starting git sync service")
            logger.info(f"Repository: {self.repo_url}")
            logger.info(f"Local path: {self.local_path}")
            logger.info(f"Branch: {self.branch}")
            logger.info(f"Sync interval: {self.sync_interval} minutes")

            # TODO : Need to implement max retry and backoff strategy, eg : jitter + exponential backoff
            while True:
                try:
                    self.sync_git_repo()
                except Exception as e:
                    logger.error(f"Error during sync: {str(e)}")
        

                if once:
                    logger.info("Single sync completed")
                    break

                logger.info(f"Next sync in {self.sync_interval} minutes")
                time.sleep(self.sync_interval * 60)

        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        except Exception as e:
            logger.error(f"Error in sync service: {str(e)}")
            raise


@click.command()
@click.option("--repo-url", "-r", default=DEFAULT_REPO_URL, help="URL of the git repository")
@click.option("--local-path", "-l", default=DEFAULT_LOCAL_PATH, help="Local path to sync the repository")
@click.option("--branch", "-b", default=DEFAULT_BRANCH, help="Branch to sync")
@click.option("--interval", "-i", default=DEFAULT_SYNC_INTERVAL, help="Sync interval in minutes", type=int)
@click.option("--once", is_flag=True, help="Run sync once and exit")

def main(repo_url: str, local_path: str, branch: str, interval: int, once: bool) -> None:
    """Git Repository Sync Service

    Keeps a local git repository in sync with its remote by periodically pulling changes.
    """
    try:
        # Expand local path
        local_path = os.path.expanduser(local_path)

        # Initialize and start service
        service = SyncService(repo_url=repo_url, local_path=local_path, branch=branch, sync_interval=interval)

        service.start(once=once)

    except KeyboardInterrupt:
        click.echo("\nShutting down...")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
