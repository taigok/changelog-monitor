"""Main monitoring script for CHANGELOG updates."""

import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

load_dotenv()

from fetcher import Fetcher
from notifier import Notifier
from translator import Translator


class SnapshotManager:
    """Manages snapshots of CHANGELOG files."""

    def __init__(self, snapshots_dir: str = "snapshots"):
        """Initialize the SnapshotManager.

        Args:
            snapshots_dir: Directory to store snapshots
        """
        self.snapshots_dir = Path(snapshots_dir)
        self.snapshots_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def get_snapshot_path(self, owner: str, repo: str) -> Path:
        """Get the path to a snapshot file.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Path to the snapshot file
        """
        filename = f"{owner}_{repo}_CHANGELOG.json"
        return self.snapshots_dir / filename

    def load_snapshot(self, owner: str, repo: str) -> Optional[dict]:
        """Load existing snapshot.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Snapshot data or None if doesn't exist
        """
        path = self.get_snapshot_path(owner, repo)
        if not path.exists():
            self.logger.info(f"No snapshot found for {owner}/{repo}")
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                snapshot = json.load(f)
            self.logger.info(f"Loaded snapshot for {owner}/{repo}")
            return snapshot
        except Exception as e:
            self.logger.error(f"Error loading snapshot: {e}")
            return None

    def save_snapshot(
        self,
        owner: str,
        repo: str,
        file_path: str,
        branch: str,
        content: str,
    ) -> None:
        """Save snapshot.

        Args:
            owner: Repository owner
            repo: Repository name
            file_path: File path
            branch: Branch name
            content: File content
        """
        snapshot = {
            "repository": {
                "owner": owner,
                "repo": repo,
                "file": file_path,
                "branch": branch,
            },
            "content_hash": self.calculate_hash(content),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "last_checked": datetime.now(timezone.utc).isoformat(),
        }

        path = self.get_snapshot_path(owner, repo)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved snapshot for {owner}/{repo}")
        except Exception as e:
            self.logger.error(f"Error saving snapshot: {e}")

    def calculate_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content.

        Args:
            content: Content to hash

        Returns:
            Hex digest of the hash
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def update_last_checked(self, owner: str, repo: str) -> None:
        """Update the last_checked timestamp.

        Args:
            owner: Repository owner
            repo: Repository name
        """
        snapshot = self.load_snapshot(owner, repo)
        if snapshot:
            snapshot["last_checked"] = datetime.now(timezone.utc).isoformat()
            path = self.get_snapshot_path(owner, repo)
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(snapshot, f, indent=2, ensure_ascii=False)
            except Exception as e:
                self.logger.error(f"Error updating last_checked: {e}")


class ChangelogMonitor:
    """Main monitoring class."""

    def __init__(self, config_path: str = "config/repositories.yml"):
        """Initialize the monitor.

        Args:
            config_path: Path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.snapshot_manager = SnapshotManager()

        # Initialize modules
        try:
            self.fetcher = Fetcher()
            self.translator = Translator(
                model_name=self.config["translation"]["model"],
                temperature=self.config["translation"]["temperature"],
            )
            self.notifier = Notifier()
        except ValueError as e:
            self.logger.error(f"Initialization error: {e}")
            sys.exit(1)

    def _load_config(self, config_path: str) -> dict:
        """Load configuration file.

        Args:
            config_path: Path to config file

        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            self.logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            sys.exit(1)

    def run(self) -> None:
        """Run the monitoring process."""
        self.logger.info("=== Changelog Monitor Started ===")

        repositories = self.config.get("repositories", [])
        if not repositories:
            self.logger.warning("No repositories configured")
            return

        stats = {"total": 0, "success": 0, "no_changes": 0, "failed": 0}

        for repo_config in repositories:
            stats["total"] += 1

            # Check if enabled
            if not repo_config.get("enabled", True):
                self.logger.info(f"Skipping disabled repository: {repo_config['name']}")
                continue

            try:
                self._process_repository(repo_config)
                stats["success"] += 1
            except NoChangesError:
                stats["no_changes"] += 1
            except Exception as e:
                self.logger.error(f"Failed to process {repo_config['name']}: {e}")
                stats["failed"] += 1

        # Print summary
        self.logger.info("\n=== Summary ===")
        self.logger.info(f"Total: {stats['total']} repositories")
        self.logger.info(f"Success: {stats['success']}")
        self.logger.info(f"No changes: {stats['no_changes']}")
        self.logger.info(f"Failed: {stats['failed']}")

    def _process_repository(self, repo_config: dict) -> None:
        """Process a single repository.

        Args:
            repo_config: Repository configuration

        Raises:
            NoChangesError: If no changes detected
            Exception: If processing fails
        """
        name = repo_config["name"]
        owner = repo_config["owner"]
        repo = repo_config["repo"]
        file_path = repo_config["file"]
        branch = repo_config.get("branch", "main")

        self.logger.info(f"\nChecking: {name}")

        # Fetch current content
        current_content = self.fetcher.fetch_changelog(owner, repo, file_path, branch)
        if current_content is None:
            raise Exception("Failed to fetch CHANGELOG")

        # Load snapshot
        snapshot = self.snapshot_manager.load_snapshot(owner, repo)

        # Check for changes
        current_hash = self.snapshot_manager.calculate_hash(current_content)

        if snapshot and snapshot.get("content_hash") == current_hash:
            self.logger.info("  ⏭️  No changes detected")
            self.snapshot_manager.update_last_checked(owner, repo)
            raise NoChangesError()

        self.logger.info("  ✅ Changes detected")

        # Extract diff
        previous_content = None
        if snapshot:
            # We don't store the full content, so we'll treat this as a full update
            # In a production system, you might want to store the previous content
            pass

        diff = self.fetcher.extract_diff(current_content, previous_content)
        if not diff.strip():
            self.logger.info("  ⏭️  No meaningful diff")
            self.snapshot_manager.update_last_checked(owner, repo)
            raise NoChangesError()

        self.logger.info(f"  📝 Diff extracted ({len(diff.split(chr(10)))} lines)")

        # Translate
        translated = self.translator.translate(diff, name)
        self.logger.info("  🌐 Translation completed")

        # Send notification
        repo_url = f"https://github.com/{owner}/{repo}/blob/{branch}/{file_path}"
        success = self.notifier.send(name, translated, repo_url)

        if success:
            self.logger.info("  📤 Discord notification sent")
        else:
            raise Exception("Failed to send notification")

        # Save snapshot
        self.snapshot_manager.save_snapshot(owner, repo, file_path, branch, current_content)
        self.logger.info("  💾 Snapshot updated")


class NoChangesError(Exception):
    """Exception raised when no changes are detected."""

    pass


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    """Main entry point."""
    setup_logging()

    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    monitor = ChangelogMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
