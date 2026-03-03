"""
agents/campaign_agent.py — Campaign creation, outreach drafting, follow-up sequences.

Handles Steps 7c, 8, 9: Campaign creation + follow-up sequences.
"""
from typing import Optional, List

from agents.base_agent import BaseAgent
from core.deal import Deal
from integrations.claude_client import ClaudeClient
from prompts.outreach_drafting import (
    OUTREACH_DRAFT_PROMPT,
    FOLLOWUP_PROMPT,
    MEETALFRED_SEQUENCE_PROMPT,
)


class CampaignAgent(BaseAgent):
    """Agent responsible for outreach message drafting and campaign creation."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        super().__init__(claude_client)

    def draft_outreach_messages(self, deal: Deal, investor: dict) -> dict:
        """
        Generate 6 platform-specific outreach messages for a specific investor.

        Args:
            deal: Current Deal object.
            investor: Investor dict with name, firm, fit info.

        Returns:
            Dict with 6 messages keyed by platform.
        """
        investor_name = investor.get("full_name", "Investor")
        investor_firm = investor.get("firm", "")
        self.logger.info(
            f"[{deal.deal_id}] Drafting outreach messages for {investor_name} @ {investor_firm}"
        )

        company_bullets = (
            f"- Company: {deal.company_name}\n"
            f"- Industry: {deal.industry}\n"
            f"- Raise: ${deal.raise_amount:,.0f}\n"
            f"- Website: {deal.company_website}"
        )
        fit_bullets = investor.get("why_good_fit", f"Strong fit based on {deal.industry} focus")
        match_explanation = investor.get("match_explanation", {}) or {}
        recent_signals = investor.get("recent_signals", []) or []

        # Enrich fit context with explainable matching reasons and recent signals.
        if isinstance(match_explanation, dict):
            reason_lines = match_explanation.get("reasons", [])[:3]
            if reason_lines:
                fit_bullets = (
                    f"{fit_bullets}\n"
                    + "\n".join(f"- Match reason: {r}" for r in reason_lines)
                )

        if recent_signals:
            signal_lines = []
            for sig in recent_signals[:2]:
                if isinstance(sig, dict):
                    txt = sig.get("text", "")
                    src = sig.get("source_type", "signal")
                    if txt:
                        signal_lines.append(f"- Recent {src}: {txt}")
            if signal_lines:
                fit_bullets = f"{fit_bullets}\n" + "\n".join(signal_lines)

        prompt = OUTREACH_DRAFT_PROMPT.format(
            investor_name=investor_name,
            investor_firm=investor_firm,
            company_bullets=company_bullets,
            fit_bullets=fit_bullets,
        )

        result = self.generate_json(prompt)
        messages = result.get("messages", result)

        # Validate all 6 platforms are present
        expected_platforms = ["web_contact_form", "linkedin", "email", "sms", "whatsapp", "twitter_dm"]
        missing_platforms = [p for p in expected_platforms if p not in messages]
        if missing_platforms:
            self.logger.warning(
                f"[{deal.deal_id}] Missing message platforms for {investor_name}: {missing_platforms}"
            )

        return {
            "investor_name": investor_name,
            "investor_firm": investor_firm,
            "messages": messages,
        }

    def generate_followup_sequence(self, deal: Deal, investor: dict, week: int) -> dict:
        """
        Generate a weekly follow-up message for a specific investor on each platform.

        Platform schedule:
        - Wednesday: X
        - Thursday: SMS / WhatsApp
        - Friday: Email
        - Saturday: LinkedIn

        Args:
            deal: Current Deal object.
            investor: Investor dict.
            week: Current outreach week number (1-12).

        Returns:
            Dict with per-platform follow-up messages for the given week.
        """
        investor_name = investor.get("full_name", "Investor")
        self.logger.info(
            f"[{deal.deal_id}] Generating week {week} follow-up for {investor_name}"
        )

        platform_schedule = {
            "wednesday": "x_twitter",
            "thursday_sms": "sms",
            "thursday_whatsapp": "whatsapp",
            "friday": "email",
            "saturday": "linkedin",
        }

        progress_update = f"Week {week} update: continuing to build traction in the {deal.industry} market."
        message_history = f"Initial outreach sent. Week {week - 1} follow-up completed." if week > 1 else "Initial outreach sent."

        week_messages = {}
        for day, platform in platform_schedule.items():
            prompt = FOLLOWUP_PROMPT.format(
                week_number=week,
                investor_name=investor_name,
                company_name=deal.company_name,
                progress_update=progress_update,
                platform=platform,
                message_history=message_history,
            )
            try:
                result = self.generate_json(prompt)
                week_messages[platform] = result
            except Exception as e:
                self.logger.warning(
                    f"[{deal.deal_id}] Failed to generate {platform} follow-up: {e}"
                )
                week_messages[platform] = {"platform": platform, "error": str(e)}

        return {
            "week": week,
            "investor_name": investor_name,
            "messages": week_messages,
        }

    def create_meetalfred_campaign(self, deal: Deal, investors: List[dict]) -> dict:
        """
        Generate a MeetAlfred campaign structure with LinkedIn message sequence.

        Args:
            deal: Current Deal object.
            investors: List of target investor dicts.

        Returns:
            Campaign structure dict ready for MeetAlfred API.
        """
        self.logger.info(
            f"[{deal.deal_id}] Creating MeetAlfred campaign for {len(investors)} investors"
        )

        investor_profile = (
            f"Active investors in {deal.industry} sector, "
            f"typically writing checks between $250K-$2M at seed stage."
        )

        prompt = MEETALFRED_SEQUENCE_PROMPT.format(
            company_name=deal.company_name,
            investor_profile=investor_profile,
            industry=deal.industry,
        )

        sequence = self.generate_json(prompt)

        campaign = {
            "name": f"{deal.company_name} — Investor Outreach Campaign",
            "deal_id": deal.deal_id,
            "target_count": len(investors),
            "sequence": sequence.get("sequence", []),
            "ab_variants": sequence.get("ab_variants", {}),
            "status": "draft_pending_review",
            "notes": "REQUIRES Phil approval before launch. Das to execute after approval.",
        }

        return campaign

    def generate_ab_variants(self, message: str) -> tuple:
        """
        Generate two A/B test variants of a connection request message.

        Args:
            message: Original message to create variants from.

        Returns:
            Tuple of (variant_a, variant_b) strings.
        """
        prompt = (
            f"Create 2 distinct A/B test variants of this LinkedIn connection request message. "
            f"Keep both under 300 characters. Make them meaningfully different in approach.\n\n"
            f"Original:\n{message}\n\n"
            f"Return JSON: {{\"variant_a\": \"\", \"variant_b\": \"\"}}"
        )
        result = self.generate_json(prompt)
        return result.get("variant_a", message), result.get("variant_b", message)
