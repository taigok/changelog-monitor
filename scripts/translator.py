"""Gemini API translator module."""

import logging
import os
import time
from typing import Optional

from google import genai
from google.genai import types


class Translator:
    """Translates technical documents using Gemini API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.3,
    ):
        """Initialize the Translator.

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model_name: Model name to use
            temperature: Temperature parameter for generation
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        self.model_name = model_name
        self.temperature = temperature
        self.logger = logging.getLogger(__name__)

        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)

    def translate(self, text: str, repo_name: str) -> str:
        """Translate text to Japanese.

        Args:
            text: Text to translate
            repo_name: Repository name for context

        Returns:
            Translated text in Japanese
        """
        if not text.strip():
            return text

        prompt = self._build_prompt(text, repo_name)

        try:
            self.logger.info(f"Translating {len(text)} characters for {repo_name}")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=2048,
                ),
            )

            translated = response.text.strip()
            self.logger.info(f"Translation completed: {len(translated)} characters")
            return translated

        except Exception as e:
            error_msg = str(e)

            # Handle rate limiting
            if "429" in error_msg or "quota" in error_msg.lower():
                self.logger.warning("Rate limit hit, waiting 3 seconds and retrying...")
                time.sleep(3)
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=self.temperature,
                            max_output_tokens=2048,
                        ),
                    )
                    translated = response.text.strip()
                    self.logger.info("Retry successful")
                    return translated
                except Exception as retry_error:
                    self.logger.error(f"Retry failed: {retry_error}")
                    return f"[翻訳失敗] {text}"

            # Other errors
            self.logger.error(f"Translation error: {e}")
            return f"[翻訳失敗] {text}"

    def _build_prompt(self, text: str, repo_name: str) -> str:
        """Build translation prompt.

        Args:
            text: Text to translate
            repo_name: Repository name

        Returns:
            Formatted prompt
        """
        return f"""あなたは技術文書の翻訳専門家です。
以下のルールに従って、{repo_name}のCHANGELOG差分を日本語に翻訳してください。

【翻訳ルール】
1. 技術的に正確に翻訳する
2. 以下は英語のまま保持:
   - バージョン番号 (v2.0.74等)
   - API名、SDK名、CLI名
   - コマンド、関数名、クラス名
   - ファイル名、パス
   - URL
   - コードブロック内のテキスト
3. 日本語として自然な表現にする
4. 箇条書きの構造は保持する
5. マークダウン記法は保持する

【翻訳対象】
{text}"""
