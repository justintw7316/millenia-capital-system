"""
agents/funding_agent.py — Alternative funding source research and outreach.

Handles Step 3: Alternative funding source research.
"""
from typing import List, Optional

from agents.base_agent import BaseAgent
from core.deal import Deal
from integrations.claude_client import ClaudeClient
from prompts.funding_sources import ALT_FUNDING_PROMPT, ALT_FUNDING_EMAIL_PROMPT


class FundingAgent(BaseAgent):
    """Agent responsible for alternative funding source discovery and outreach drafting."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        super().__init__(claude_client)

    def find_alt_sources(self, deal: Deal) -> List[dict]:
        """
        Find 10 ranked alternative funding sources (grants, loans, sponsored capital).

        Args:
            deal: Current Deal object.

        Returns:
            List of up to 10 funding source dicts, ranked by fit.
        """
        self.logger.info(
            f"[{deal.deal_id}] Searching for alternative funding sources for {deal.company_name}"
        )
        prompt = ALT_FUNDING_PROMPT.format(
            company_name=deal.company_name,
            company_profile=deal.company_profile_text(),
        )
        result = self.generate_json(prompt)

        # Handle list or wrapped dict
        if isinstance(result, list):
            sources = result
        elif isinstance(result, dict) and "sources" in result:
            sources = result["sources"]
        else:
            sources = []
            self.logger.warning(f"[{deal.deal_id}] Unexpected funding sources response shape")

        # Sort by rank
        sources.sort(key=lambda x: x.get("rank", 99))

        # Retry with broader prompt if fewer than 10
        if len(sources) < 10:
            self.logger.warning(
                f"[{deal.deal_id}] Only {len(sources)} alt funding sources found — "
                f"retrying with broader prompt"
            )
            broader_prompt = ALT_FUNDING_PROMPT.format(
                company_name=deal.company_name,
                company_profile=(
                    deal.company_profile_text()
                    + "\nNote: Include general seed-stage sources for any tech startup "
                    "if industry-specific sources are limited."
                ),
            )
            retry_result = self.generate_json(broader_prompt)
            if isinstance(retry_result, list):
                sources = retry_result
            elif isinstance(retry_result, dict) and "sources" in retry_result:
                sources = retry_result["sources"]

        self.logger.info(
            f"[{deal.deal_id}] Found {len(sources)} alternative funding sources"
        )
        return sources[:10]

    def draft_outreach_email(self, deal: Deal, source: dict) -> dict:
        """
        Draft a custom outreach email for a specific alternative funding source.

        Args:
            deal: Current Deal object.
            source: Funding source dict with organization_name, contact_name, etc.

        Returns:
            Dict with 'subject' and 'body'.
        """
        source_name = source.get("organization_name", "Unknown Organization")
        contact_name = source.get("contact_name", "Team")
        self.logger.info(
            f"[{deal.deal_id}] Drafting outreach email for {source_name}"
        )
        prompt = ALT_FUNDING_EMAIL_PROMPT.format(
            source_name=source_name,
            company_name=deal.company_name,
            contact_name=contact_name,
            funding_type=source.get("funding_type", "alternative funding"),
        )
        result = self.generate_json(prompt)
        return result
