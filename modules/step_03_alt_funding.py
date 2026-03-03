"""
modules/step_03_alt_funding.py — Step 3: Alternative Funding Sources

AI-generated list of 10 alternative funding sources with custom outreach emails.
"""
import json
import csv
from datetime import datetime
from typing import Tuple

from core.deal import Deal
from core.logger import get_logger
from agents.funding_agent import FundingAgent
from config import OUTPUT_DIR

logger = get_logger(__name__)


def run(deal: Deal, config: dict) -> Tuple[Deal, dict]:
    """
    Step 3: Find alternative funding sources, draft outreach emails, and MeetAlfred draft.
    """
    logger.info(f"[{deal.deal_id}] ▶ Step 3: Alternative Funding Sources")

    errors = []
    human_actions = []
    outputs = {}

    output_dir = OUTPUT_DIR / deal.deal_id
    output_dir.mkdir(parents=True, exist_ok=True)

    agent = FundingAgent()

    # ── Find alternative funding sources ──────────────────────────────────────
    try:
        sources = agent.find_alt_sources(deal)
        logger.info(f"[{deal.deal_id}] Found {len(sources)} alternative funding sources")

        # Save sources JSON
        sources_path = output_dir / "alt_funding_sources.json"
        with open(sources_path, "w") as f:
            json.dump({"deal_id": deal.deal_id, "sources": sources, "generated_at": datetime.utcnow().isoformat()}, f, indent=2)
        outputs["alt_funding_sources"] = str(sources_path)

        # Save contact CSV
        csv_path = output_dir / "alt_funding_contacts.csv"
        _write_contacts_csv(sources, csv_path)
        outputs["alt_funding_csv"] = str(csv_path)

    except Exception as e:
        errors.append(f"Alternative funding source search failed: {e}")
        logger.error(f"[{deal.deal_id}] Alt funding search error: {e}")
        sources = []

    # ── Draft outreach emails ─────────────────────────────────────────────────
    emails = []
    if sources:
        try:
            email_lines = [f"# Alternative Funding Outreach Emails — {deal.company_name}\n"]
            email_lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d')}\n\n---\n")

            for source in sources:
                source_name = source.get("organization_name", "Unknown")
                try:
                    email = agent.draft_outreach_email(deal, source)
                    emails.append({"source": source_name, **email})
                    email_lines.append(f"## {source_name}\n")
                    email_lines.append(f"**To:** {source.get('contact_name', 'Team')} <{source.get('email', 'N/A')}>")
                    email_lines.append(f"**Subject:** {email.get('subject', '')}\n")
                    email_lines.append(email.get("body", ""))
                    email_lines.append("\n---\n")
                    logger.debug(f"[{deal.deal_id}] Email drafted for {source_name}")
                except Exception as e:
                    errors.append(f"Email draft failed for {source_name}: {e}")
                    logger.warning(f"[{deal.deal_id}] Email draft error for {source_name}: {e}")

            emails_path = output_dir / "alt_funding_emails.md"
            emails_path.write_text("\n".join(email_lines))
            outputs["alt_funding_emails"] = str(emails_path)
            logger.info(f"[{deal.deal_id}] {len(emails)} outreach emails drafted")

        except Exception as e:
            errors.append(f"Email drafting failed: {e}")
            logger.error(f"[{deal.deal_id}] Email drafting error: {e}")

    # ── Generate MeetAlfred LinkedIn campaign draft ────────────────────────────
    try:
        ma_draft = _generate_meetalfred_draft(deal, sources)
        ma_path = output_dir / "alt_funding_meetalfred_draft.md"
        ma_path.write_text(ma_draft)
        outputs["alt_funding_meetalfred"] = str(ma_path)
    except Exception as e:
        errors.append(f"MeetAlfred draft generation failed: {e}")
        logger.warning(f"[{deal.deal_id}] MeetAlfred draft error: {e}")

    human_actions.append(
        "Review alt_funding_sources.json — verify contacts are correct before outreach."
    )

    deal.log_step("03", "completed", f"Found {len(sources)} alt funding sources, {len(emails)} emails drafted.", outputs)

    return deal, {
        "success": len(errors) == 0,
        "output": outputs,
        "errors": errors,
        "human_actions_required": human_actions,
    }


def _write_contacts_csv(sources: list, path) -> None:
    """Write funding sources to CSV file."""
    fieldnames = [
        "rank", "organization_name", "contact_name", "email", "phone",
        "website", "funding_type", "typical_amount_range", "why_good_fit"
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sources)


def _generate_meetalfred_draft(deal: Deal, sources: list) -> str:
    """Generate a MeetAlfred LinkedIn campaign draft for alternative funding sources."""
    lines = [
        f"# MeetAlfred LinkedIn Campaign — Alternative Funding Sources",
        f"**Company:** {deal.company_name}",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d')}",
        "",
        "## Campaign Overview",
        "- **Objective:** Connect with alternative funding sources on LinkedIn",
        "- **Target:** Program officers, grant managers, lending officers",
        "- **Sequence:** 3-message sequence (connection → follow-up 1 → follow-up 2)",
        "",
        "## Message Templates",
        "",
        "### Connection Request (under 300 characters)",
        f"Hi {{{{first_name}}}}, I lead {deal.company_name}, a {deal.industry} company raising ${deal.raise_amount:,.0f}. "
        f"I'd love to explore whether [Organization] could be a fit. Worth a quick connect?",
        "",
        "### Follow-Up 1 (3 days after connection)",
        f"Hi {{{{first_name}}}}, thanks for connecting. {deal.company_name} is tackling [key problem] in {deal.industry}. "
        f"We're raising ${deal.raise_amount:,.0f} and exploring grant/funding opportunities that align with your mission. "
        f"Would you have 15 minutes to discuss?",
        "",
        "### Follow-Up 2 (7 days after Follow-Up 1)",
        f"Hi {{{{first_name}}}}, following up on my last message. I've attached a brief overview of {deal.company_name}. "
        f"Happy to share our full deck under NDA. Any interest in connecting?",
        "",
        "## Target Sources",
        "",
    ]

    for source in sources[:10]:
        lines.append(f"- **{source.get('organization_name', 'N/A')}** — {source.get('contact_name', 'N/A')} | {source.get('email', 'N/A')}")

    lines.extend([
        "",
        "## Launch Checklist",
        "- [ ] Review and personalize message templates",
        "- [ ] Upload target contact list to MeetAlfred",
        "- [ ] Set sending schedule (Mon–Fri, 9am–5pm target timezone)",
        "- [ ] Phil approval before launch",
        "- [ ] Das to execute campaign launch",
    ])

    return "\n".join(lines)
