"""
agents/document_agent.py — Document review, tear sheet, and pitch deck generation.

Handles Step 2: Data room audit, document QA, Sequoia-grade review.
"""
from typing import Optional

from agents.base_agent import BaseAgent
from core.deal import Deal
from integrations.claude_client import ClaudeClient
from prompts.document_review import (
    SEQUOIA_REVIEW_PROMPT,
    TEAR_SHEET_OUTLINE_PROMPT,
    PITCH_DECK_OUTLINE_PROMPT,
    FINANCIAL_REVIEW_PROMPT,
)


class DocumentAgent(BaseAgent):
    """Agent responsible for all document generation and quality review."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        super().__init__(claude_client)

    def generate_tear_sheet_outline(self, deal: Deal) -> str:
        """
        Generate a 1-2 page investor tear sheet outline for the deal.

        Args:
            deal: Current Deal object.

        Returns:
            Markdown string with the tear sheet content.
        """
        self.logger.info(f"[{deal.deal_id}] Generating tear sheet outline for {deal.company_name}")
        prompt = TEAR_SHEET_OUTLINE_PROMPT.format(
            company_name=deal.company_name,
            company_profile=deal.company_profile_text(),
        )
        result = self.generate_text(prompt)
        self.logger.info(f"[{deal.deal_id}] Tear sheet outline generated — {len(result)} chars")
        return result

    def generate_pitch_deck_outline(self, deal: Deal) -> dict:
        """
        Generate an 11-slide pitch deck structure with content guidance per slide.

        Args:
            deal: Current Deal object.

        Returns:
            Dict with 'slides' list.
        """
        self.logger.info(f"[{deal.deal_id}] Generating pitch deck outline for {deal.company_name}")
        prompt = PITCH_DECK_OUTLINE_PROMPT.format(
            company_name=deal.company_name,
            company_profile=deal.company_profile_text(),
        )
        result = self.generate_json(prompt)
        self.logger.info(
            f"[{deal.deal_id}] Pitch deck outline generated — "
            f"{len(result.get('slides', []))} slides"
        )
        return result

    def sequoia_review(self, deal: Deal) -> dict:
        """
        Grade the tear sheet and pitch deck from a Sequoia Capital perspective.

        Args:
            deal: Current Deal object.

        Returns:
            Dict with grades, revision notes, and investment readiness rating.
        """
        self.logger.info(f"[{deal.deal_id}] Running Sequoia review for {deal.company_name}")
        prompt = SEQUOIA_REVIEW_PROMPT.format(
            company_name=deal.company_name,
            company_profile=deal.company_profile_text(),
        )
        result = self.generate_json(prompt)
        overall = result.get("overall_score", 0)
        readiness = result.get("investment_readiness", "unknown")
        self.logger.info(
            f"[{deal.deal_id}] Sequoia review complete — "
            f"overall_score={overall}, readiness={readiness}"
        )
        return result

    def review_financials(self, deal: Deal) -> dict:
        """
        Check financial projections for required components (FCFF, WACC, etc.).

        Args:
            deal: Current Deal object.

        Returns:
            Dict with component status and action items.
        """
        self.logger.info(f"[{deal.deal_id}] Reviewing financials for {deal.company_name}")
        prompt = FINANCIAL_REVIEW_PROMPT.format(
            company_name=deal.company_name,
            company_profile=deal.company_profile_text(),
        )
        result = self.generate_json(prompt)
        missing = result.get("missing_items", [])
        if missing:
            self.logger.warning(f"[{deal.deal_id}] Missing financial components: {missing}")
        return result
