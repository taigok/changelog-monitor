"""GitHub CHANGELOG fetcher module."""

import logging
import re
from typing import Optional

import requests


class Fetcher:
    """Fetches CHANGELOG files from GitHub repositories."""

    def __init__(self, timeout: int = 10):
        """Initialize the Fetcher.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def fetch_changelog(
        self,
        owner: str,
        repo: str,
        file_path: str,
        branch: str = "main",
    ) -> Optional[str]:
        """Fetch CHANGELOG content from GitHub.

        Args:
            owner: Repository owner
            repo: Repository name
            file_path: Path to the file (e.g., CHANGELOG.md)
            branch: Branch name

        Returns:
            File content as string, or None if failed
        """
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"

        try:
            self.logger.info(f"Fetching {owner}/{repo}/{file_path} from branch {branch}")
            response = requests.get(url, timeout=self.timeout)

            if response.status_code == 404:
                self.logger.warning(f"File not found: {url}")
                return None

            response.raise_for_status()
            content = response.text
            self.logger.info(f"Successfully fetched {len(content)} characters")
            return content

        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout while fetching {url}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def extract_latest_version_section(self, content: str) -> Optional[str]:
        """Extract the latest version section from CHANGELOG.

        Args:
            content: CHANGELOG content

        Returns:
            Latest version section or None if no version found
        """
        # Pattern to match version headers like:
        # ## 2.1.6, ## [2.1.6], # v2.1.6, ## Version 2.1.6
        version_pattern = r"^##?\s+(?:\[)?(?:v|version\s+)?(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)"

        lines = content.split("\n")
        start_idx = None
        end_idx = None

        # Find the first version header
        for i, line in enumerate(lines):
            if re.match(version_pattern, line.strip(), re.IGNORECASE):
                if start_idx is None:
                    start_idx = i
                    self.logger.info(f"Found first version at line {i}: {line.strip()}")
                else:
                    # Found the next version, so the first section ends here
                    end_idx = i
                    break

        if start_idx is None:
            self.logger.warning("No version section found in CHANGELOG")
            return None

        # If no second version found, take until the end
        if end_idx is None:
            end_idx = len(lines)

        # Extract the section
        section_lines = lines[start_idx:end_idx]
        result = "\n".join(section_lines).strip()

        self.logger.info(f"Extracted version section ({end_idx - start_idx} lines)")
        return result

    def extract_diff(
        self,
        current: str,
        previous: Optional[str],
        max_lines: int = 50,
    ) -> str:
        """Extract the difference between current and previous content.

        Args:
            current: Current file content
            previous: Previous file content (None for first run)
            max_lines: Maximum number of lines to extract

        Returns:
            Diff text containing newly added lines (latest version section only)
        """
        if previous is None:
            # First run: extract latest version section
            latest_section = self.extract_latest_version_section(current)
            if latest_section:
                self.logger.info("First run: extracted latest version section")
                return latest_section
            # Fallback to first max_lines if no version found
            lines = current.split("\n")
            result = "\n".join(lines[:max_lines])
            self.logger.info(f"First run: extracted {min(len(lines), max_lines)} lines")
            return result

        # Extract latest version section from current
        current_latest = self.extract_latest_version_section(current)
        previous_latest = self.extract_latest_version_section(previous)

        # If we have a new version section that's different from the previous one
        if current_latest and current_latest != previous_latest:
            self.logger.info("New version detected")
            return current_latest

        # If no change in version section, return empty
        self.logger.info("No new version section detected")
        return ""
