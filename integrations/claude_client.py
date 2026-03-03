"""
integrations/claude_client.py — Anthropic Claude API client (REAL).

Uses ANTHROPIC_API_KEY from environment.
Default model: claude-sonnet-4-5
"""
import json
import time
import re
from typing import Optional

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS, AI_MAX_RETRIES, AI_RETRY_BASE_DELAY
from core.logger import get_logger

logger = get_logger(__name__)


class ClaudeClient:
    """Thin wrapper around the Anthropic SDK with retry logic and JSON parsing."""

    def __init__(self):
        if not ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY is not set — Claude calls will fail.")
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = CLAUDE_MODEL
        self.max_tokens = CLAUDE_MAX_TOKENS

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Call Claude and return the text response.

        Retries up to AI_MAX_RETRIES times with exponential backoff on failure.

        Args:
            prompt: User-facing prompt text.
            system: Optional system prompt.

        Returns:
            String response from Claude.

        Raises:
            RuntimeError: If all retries are exhausted.
        """
        messages = [{"role": "user", "content": prompt}]
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        last_error = None
        for attempt in range(1, AI_MAX_RETRIES + 1):
            try:
                logger.debug(f"Claude API call attempt {attempt}/{AI_MAX_RETRIES} — model={self.model}")
                response = self.client.messages.create(**kwargs)
                text = response.content[0].text
                logger.debug(
                    f"Claude response received — input_tokens={response.usage.input_tokens}, "
                    f"output_tokens={response.usage.output_tokens}"
                )
                return text
            except anthropic.APIError as e:
                last_error = e
                delay = AI_RETRY_BASE_DELAY ** attempt
                logger.warning(f"Claude API error (attempt {attempt}): {e}. Retrying in {delay}s…")
                time.sleep(delay)

        raise RuntimeError(
            f"Claude API failed after {AI_MAX_RETRIES} attempts. Last error: {last_error}"
        )

    def generate_json(self, prompt: str, system: Optional[str] = None) -> dict:
        """
        Call Claude expecting a JSON response. Parses and validates the JSON.
        Retries on JSON parse failure (up to AI_MAX_RETRIES total attempts).

        Args:
            prompt: Prompt that instructs Claude to respond with JSON.
            system: Optional system prompt.

        Returns:
            Parsed dict or list.

        Raises:
            RuntimeError: If JSON cannot be parsed after all retries.
        """
        json_system = (system or "") + "\nYou must respond with valid JSON only — no prose, no markdown fences."
        json_prompt = prompt + "\n\nRespond with valid JSON only."

        last_error = None
        for attempt in range(1, AI_MAX_RETRIES + 1):
            try:
                raw = self.generate(json_prompt, system=json_system)
                # Strip markdown code fences if present
                cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
                cleaned = re.sub(r"\s*```$", "", cleaned)
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"JSON parse failure (attempt {attempt}): {e}. Retrying…")

        raise RuntimeError(
            f"Claude returned invalid JSON after {AI_MAX_RETRIES} attempts. Last error: {last_error}"
        )
