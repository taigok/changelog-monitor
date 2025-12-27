"""GitHub CHANGELOG fetcher module."""

import logging
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
            Diff text containing newly added lines
        """
        if previous is None:
            # First run: return first max_lines
            lines = current.split("\n")
            result = "\n".join(lines[:max_lines])
            self.logger.info(f"First run: extracted {min(len(lines), max_lines)} lines")
            return result

        # Extract new lines from the beginning
        current_lines = current.split("\n")
        previous_lines = previous.split("\n")

        # Find where they diverge
        diff_lines = []
        for i, line in enumerate(current_lines):
            if i >= len(previous_lines) or line != previous_lines[i]:
                diff_lines.append(line)
            else:
                # Once we find a matching line at the same position,
                # we've found where the old content starts
                break

        # Limit to max_lines
        result_lines = diff_lines[:max_lines]
        result = "\n".join(result_lines)

        if diff_lines:
            self.logger.info(f"Extracted {len(result_lines)} new lines (total new: {len(diff_lines)})")
        else:
            self.logger.info("No differences found")

        return result
