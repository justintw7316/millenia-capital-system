"""
agents/reporting_agent.py — Weekly reports, compliance summaries.

Handles Step 14: Reporting, compliance tracking, wire verification.
"""
from typing import Optional
from datetime import datetime, timedelta

from agents.base_agent import BaseAgent
from core.deal import Deal
from integrations.claude_client import ClaudeClient
from prompts.weekly_report import WEEKLY_REPORT_PROMPT, COMPLIANCE_LOG_PROMPT
from config import RESPONSE_RATE_ALERT_THRESHOLD, MEETING_CONVERSION_ALERT_THRESHOLD


class ReportingAgent(BaseAgent):
    """Agent responsible for weekly reports and compliance tracking."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        super().__init__(claude_client)

    def calculate_response_rate(self, deal: Deal) -> float:
        """
        Calculate the investor outreach response rate.

        Returns:
            Float between 0.0 and 1.0 (e.g., 0.23 = 23% response rate).
        """
        contacted = len(deal.investors_contacted)
        responded = len(deal.investors_responded)
        if contacted == 0:
            return 0.0
        return responded / contacted

    def calculate_meeting_conversion(self, deal: Deal) -> float:
        """
        Calculate meeting conversion rate (meetings / responses).

        Returns:
            Float between 0.0 and 1.0.
        """
        responded = len(deal.investors_responded)
        # Count investors in step_log with meeting_scheduled status
        meetings = sum(
            1 for entry in deal.step_log
            if entry.get("status") == "meeting_scheduled"
        )
        if responded == 0:
            return 0.0
        return meetings / responded

    def generate_weekly_report(self, deal: Deal) -> str:
        """
        Generate a full weekly progress report in markdown.

        Args:
            deal: Current Deal object.

        Returns:
            Markdown string for the weekly report.
        """
        week = deal.outreach_week or 1
        now = datetime.utcnow()
        start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")

        response_rate = self.calculate_response_rate(deal)
        meeting_conversion = self.calculate_meeting_conversion(deal)
        total_committed = sum(
            inv.get("commitment_amount", 0) for inv in deal.investors_committed
        )
        pipeline_value = sum(
            inv.get("interest_amount", 0) for inv in deal.investors_responded
            if inv not in deal.investors_committed
        )

        # New contacts this week (approximate — last 7 days)
        investors_this_week = len([
            inv for inv in deal.investors_contacted
            if inv.get("contacted_at", "")[:10] >= start_date
        ])

        completed_steps = [
            entry["step"] for entry in deal.step_log
            if entry.get("status") == "completed"
        ]

        self.logger.info(
            f"[{deal.deal_id}] Generating week {week} report — "
            f"response_rate={response_rate:.1%}, conversion={meeting_conversion:.1%}"
        )

        prompt = WEEKLY_REPORT_PROMPT.format(
            company_name=deal.company_name,
            week_number=week,
            start_date=start_date,
            end_date=end_date,
            investors_contacted_this_week=investors_this_week,
            total_investors_contacted=len(deal.investors_contacted),
            total_responded=len(deal.investors_responded),
            response_rate=response_rate,
            meetings_scheduled=len([e for e in deal.step_log if e.get("status") == "meeting_scheduled"]),
            meetings_completed=len([e for e in deal.step_log if e.get("status") == "meeting_completed"]),
            meeting_conversion=meeting_conversion,
            commitments_received=len(deal.investors_committed),
            total_committed=total_committed,
            raise_amount=deal.raise_amount,
            pipeline_value=pipeline_value,
            campaign_active=deal.campaign_active,
            outreach_week=deal.outreach_week,
            completed_steps=", ".join(completed_steps) if completed_steps else "None",
        )

        report = self.generate_text(prompt)

        # Append alerts if thresholds breached
        alerts = []
        if response_rate < RESPONSE_RATE_ALERT_THRESHOLD and len(deal.investors_contacted) >= 20:
            alerts.append(
                f"\n\n⚠️ **PHIL ALERT: Response rate is {response_rate:.1%} — below the 20% threshold.** "
                f"Review messaging and targeting immediately."
            )
        if meeting_conversion < MEETING_CONVERSION_ALERT_THRESHOLD and len(deal.investors_responded) >= 5:
            alerts.append(
                f"\n\n⚠️ **PHIL ALERT: Meeting conversion is {meeting_conversion:.1%} — below the 5% threshold.** "
                f"Consider adjusting pitch approach or investor list."
            )

        for alert in alerts:
            report += alert
            self.logger.warning(f"[{deal.deal_id}] ALERT generated: {alert[:80]}…")

        return report

    def generate_compliance_log(self, deal: Deal) -> dict:
        """
        Generate a legal document tracking and compliance log.

        Args:
            deal: Current Deal object.

        Returns:
            Dict with compliance status and action items.
        """
        self.logger.info(f"[{deal.deal_id}] Generating compliance log")

        prompt = COMPLIANCE_LOG_PROMPT.format(
            company_name=deal.company_name,
            document_status=str(deal.documents.to_dict()),
            nda_signed_by=", ".join(deal.nda_signed_by) if deal.nda_signed_by else "None",
            investors_contacted_count=len(deal.investors_contacted),
        )

        log_text = self.generate_text(prompt)

        return {
            "company_name": deal.company_name,
            "deal_id": deal.deal_id,
            "generated_at": datetime.utcnow().isoformat(),
            "document_status": deal.documents.to_dict(),
            "nda_signed_by": deal.nda_signed_by,
            "compliance_log": log_text,
            "action_items_for_dock_walls": self._extract_dock_walls_items(deal),
        }

    def _extract_dock_walls_items(self, deal: Deal) -> list:
        """Identify legal items that need Dock Walls review."""
        items = []
        docs = deal.documents
        if docs.ppm.value == "missing":
            items.append("PPM not prepared — legal review required")
        if docs.subscription_agreement.value == "missing":
            items.append("Subscription Agreement missing — needs legal draft")
        if docs.wiring_instructions.value == "missing":
            items.append("Wiring instructions not provided — legal review required")
        if docs.nda.value in ("missing", "draft"):
            items.append("NDA not approved — legal review and execution required")
        return items
