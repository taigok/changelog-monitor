"""Discord Webhook notification module."""

import logging
import os
from typing import Optional

import requests


class Notifier:
    """Sends notifications via Discord Webhook."""

    def __init__(self, webhook_url: Optional[str] = None, timeout: int = 10):
        """Initialize the Notifier.

        Args:
            webhook_url: Discord Webhook URL (defaults to DISCORD_WEBHOOK_URL env var)
            timeout: Request timeout in seconds
        """
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("DISCORD_WEBHOOK_URL environment variable is required")

        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def send(self, repo_name: str, translated_text: str, repo_url: str) -> bool:
        """Send notification to Discord.

        Args:
            repo_name: Repository name
            translated_text: Translated text
            repo_url: URL to the CHANGELOG file

        Returns:
            True if successful, False otherwise
        """
        # Truncate message if too long (Discord limit: 2000 chars for content)
        truncated_text = self.truncate_message(translated_text, max_length=1800)

        # Format message
        message = f"""📄 **{repo_name} CHANGELOG更新**

{truncated_text}

**詳細:** {repo_url}"""

        # Send to Discord Webhook
        payload = {"content": message}

        try:
            self.logger.info(f"Sending notification for {repo_name}")
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
            )

            if response.status_code == 401:
                self.logger.error("Invalid Discord Webhook URL (401)")
                return False

            if response.status_code == 404:
                self.logger.error("Discord Webhook not found (404)")
                return False

            if response.status_code == 429:
                self.logger.error("Discord rate limit exceeded (429)")
                return False

            # Discord returns 204 on success
            if response.status_code == 204:
                self.logger.info("Notification sent successfully")
                return True

            response.raise_for_status()
            self.logger.info("Notification sent successfully")
            return True

        except requests.exceptions.Timeout:
            self.logger.error("Timeout while sending notification")
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error sending notification: {e}")
            return False

    def truncate_message(self, text: str, max_length: int = 1800) -> str:
        """Truncate message to fit within length limit.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        # Try to truncate at a newline
        truncated = text[:max_length]
        last_newline = truncated.rfind("\n")

        if last_newline > max_length * 0.7:  # If newline is in the last 30%
            truncated = truncated[:last_newline]
        else:
            # Try to truncate at a space
            last_space = truncated.rfind(" ")
            if last_space > max_length * 0.7:
                truncated = truncated[:last_space]

        suffix = "...(続きはリンク先で)"
        return truncated + suffix
