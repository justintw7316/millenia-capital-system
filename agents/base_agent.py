"""
agents/base_agent.py — Base class all agents inherit from.

Handles:
- Claude API calls via claude_client.py
- Retry logic (3 attempts with exponential backoff, delegated to ClaudeClient)
- Response validation
- Token usage logging
"""
from abc import ABC
from typing import Optional

from integrations.claude_client import ClaudeClient
from core.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all Millenia Ventures AI agents.

    Subclasses implement domain-specific methods using self.claude for API calls.
    """

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """
        Args:
            claude_client: Optional shared ClaudeClient instance.
                           Creates a new one if not provided.
        """
        self.claude = claude_client or ClaudeClient()
        self.logger = get_logger(self.__class__.__name__)

    def generate_text(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Generate a text response from Claude.

        Args:
            prompt: User prompt.
            system: Optional system message.

        Returns:
            Text string from Claude.
        """
        self.logger.debug(f"generate_text | prompt_length={len(prompt)}")
        return self.claude.generate(prompt, system=system)

    def generate_json(self, prompt: str, system: Optional[str] = None) -> dict:
        """
        Generate a JSON-parsed response from Claude.

        Args:
            prompt: User prompt (should instruct Claude to return JSON).
            system: Optional system message.

        Returns:
            Parsed dict.
        """
        self.logger.debug(f"generate_json | prompt_length={len(prompt)}")
        return self.claude.generate_json(prompt, system=system)

    @staticmethod
    def _require_keys(data: dict, required: list, context: str = "") -> list:
        """
        Validate that required keys exist in a dict.

        Returns:
            List of missing key names (empty if all present).
        """
        missing = [k for k in required if k not in data or data[k] is None]
        if missing and context:
            logger.warning(f"[{context}] Missing required fields: {missing}")
        return missing
