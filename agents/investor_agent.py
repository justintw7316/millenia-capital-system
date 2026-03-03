"""
agents/investor_agent.py — Investor discovery and fit scoring.

Handles Steps 7a-7b: Investor discovery + outreach drafting.
"""
from typing import List, Optional

from agents.base_agent import BaseAgent
from core.deal import Deal
from integrations.claude_client import ClaudeClient
from prompts.investor_search import INVESTOR_SEARCH_PROMPT, INVESTOR_FIT_SCORE_PROMPT


class InvestorAgent(BaseAgent):
    """Agent responsible for finding and scoring investors."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        super().__init__(claude_client)

    def find_investors(self, deal: Deal) -> List[dict]:
        """
        Find 20 ranked investors with fit scores based on the deal profile.

        Args:
            deal: Current Deal object.

        Returns:
            List of up to 20 investor dicts, ranked by fit_score.
        """
        self.logger.info(f"[{deal.deal_id}] Searching for investors for {deal.company_name}")
        prompt = INVESTOR_SEARCH_PROMPT.format(
            company_website=deal.company_website,
            company_profile=deal.company_profile_text(),
            industry=deal.industry,
        )
        result = self.generate_json(prompt)

        # Handle both list and wrapped dict responses
        if isinstance(result, list):
            investors = result
        elif isinstance(result, dict) and "investors" in result:
            investors = result["investors"]
        else:
            self.logger.warning(
                f"[{deal.deal_id}] Unexpected investor search response shape; "
                f"attempting to use as-is"
            )
            investors = result if isinstance(result, list) else []

        # Deduplicate by email
        seen_emails = set()
        deduped = []
        removed = 0
        for inv in investors:
            email = inv.get("email", "").lower().strip()
            if email and email in seen_emails:
                removed += 1
                continue
            if email:
                seen_emails.add(email)
            deduped.append(inv)

        if removed:
            self.logger.info(f"[{deal.deal_id}] Removed {removed} duplicate investor contacts")

        # Sort by fit_score descending
        deduped.sort(key=lambda x: x.get("fit_score", 0), reverse=True)

        self.logger.info(
            f"[{deal.deal_id}] Found {len(deduped)} investors — "
            f"top fit score: {deduped[0].get('fit_score', 0) if deduped else 0}"
        )
        return deduped[:20]  # cap at 20

    def score_investor_fit(self, deal: Deal, investor: dict) -> float:
        """
        Score the fit between a specific investor and this deal (0.0 to 1.0).

        Args:
            deal: Current Deal object.
            investor: Investor dict with at minimum name, firm, thesis.

        Returns:
            Float fit score between 0.0 and 1.0.
        """
        prompt = INVESTOR_FIT_SCORE_PROMPT.format(
            company_profile=deal.company_profile_text(),
            investor_name=investor.get("full_name", "Unknown"),
            investor_firm=investor.get("firm", "Unknown"),
            investor_thesis=investor.get("investment_thesis", "Not provided"),
            investor_portfolio=", ".join(investor.get("portfolio_companies", [])),
            investor_check_size=investor.get("check_size_range", "Unknown"),
        )
        result = self.generate_json(prompt)
        score = float(result.get("fit_score", 0.5))
        score = max(0.0, min(1.0, score))  # clamp to [0,1]
        self.logger.debug(
            f"[{deal.deal_id}] Investor fit score for {investor.get('full_name')}: {score:.2f}"
        )
        return score
