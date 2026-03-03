"""
modules/step_07b_outreach_messages.py — Step 7b: Outreach Messages

Generates 6 platform-specific outreach messages per investor.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Tuple

from core.deal import Deal
from core.logger import get_logger
from agents.campaign_agent import CampaignAgent
from config import OUTPUT_DIR

logger = get_logger(__name__)


def run(deal: Deal, config: dict) -> Tuple[Deal, dict]:
    """
    Step 7b: Draft 6 platform-specific outreach messages per investor.

    Reads investor_list.json from Step 7a output.
    """
    logger.info(f"[{deal.deal_id}] ▶ Step 7b: Outreach Messages")

    errors = []
    human_actions = []
    outputs = {}

    output_dir = OUTPUT_DIR / deal.deal_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Load investor list ─────────────────────────────────────────────────────
    investor_list_path = output_dir / "investor_list.json"
    if not investor_list_path.exists():
        msg = "investor_list.json not found — run Step 7a first."
        logger.error(f"[{deal.deal_id}] {msg}")
        deal.log_step("07b", "blocked", msg)
        return deal, {
            "success": False,
            "output": {},
            "errors": [msg],
            "human_actions_required": ["Run Step 7a (Investor Discovery) before Step 7b."],
        }

    with open(investor_list_path) as f:
        investor_data = json.load(f)
    investors = investor_data.get("investors", [])

    if not investors:
        msg = "No investors in investor_list.json — cannot draft messages."
        errors.append(msg)
        deal.log_step("07b", "failed", msg)
        return deal, {
            "success": False,
            "output": {},
            "errors": [msg],
            "human_actions_required": [],
        }

    campaign_agent = CampaignAgent()
    all_messages = []

    # ── Draft messages per investor ───────────────────────────────────────────
    messages_dir = output_dir / "outreach_messages"
    messages_dir.mkdir(exist_ok=True)

    for investor in investors:
        name = investor.get("full_name", "Unknown Investor")
        firm = investor.get("firm", "")
        safe_name = name.replace(" ", "_").replace("/", "-")

        try:
            result = campaign_agent.draft_outreach_messages(deal, investor)
            all_messages.append(result)

            # Save individual investor message file
            investor_md = _format_investor_messages_md(deal, investor, result)
            investor_path = messages_dir / f"outreach_messages_{safe_name}.md"
            investor_path.write_text(investor_md)
            logger.debug(f"[{deal.deal_id}] Messages drafted for {name}")

        except Exception as e:
            errors.append(f"Message drafting failed for {name}: {e}")
            logger.warning(f"[{deal.deal_id}] Message draft error for {name}: {e}")

    # ── Save bundle ───────────────────────────────────────────────────────────
    if all_messages:
        bundle_path = output_dir / "outreach_bundle.json"
        with open(bundle_path, "w") as f:
            json.dump({
                "deal_id": deal.deal_id,
                "generated_at": datetime.utcnow().isoformat(),
                "investor_count": len(all_messages),
                "platforms": ["web_contact_form", "linkedin", "email", "sms", "whatsapp", "twitter_dm"],
                "messages": all_messages,
            }, f, indent=2)
        outputs["outreach_bundle"] = str(bundle_path)
        outputs["outreach_messages_dir"] = str(messages_dir)
        logger.info(
            f"[{deal.deal_id}] Outreach bundle created: {len(all_messages)} investors × 6 platforms"
        )

    human_actions.append(
        "Review outreach_bundle.json and individual message files before sending. "
        "No messages have been sent — this is a draft only."
    )

    deal.log_step("07b", "completed", f"Drafted outreach for {len(all_messages)} investors.", outputs)

    return deal, {
        "success": len(all_messages) > 0,
        "output": outputs,
        "errors": errors,
        "human_actions_required": human_actions,
    }


def _format_investor_messages_md(deal: Deal, investor: dict, result: dict) -> str:
    name = investor.get("full_name", "Unknown")
    firm = investor.get("firm", "")
    messages = result.get("messages", {})

    lines = [
        f"# Outreach Messages — {name} @ {firm}",
        f"**Deal:** {deal.company_name}",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d')}",
        "",
        "---",
        "",
    ]

    platform_labels = {
        "web_contact_form": "Web Contact Form",
        "linkedin": "LinkedIn Message",
        "email": "Email",
        "sms": "SMS",
        "whatsapp": "WhatsApp",
        "twitter_dm": "X (Twitter) DM",
    }

    for platform_key, label in platform_labels.items():
        msg = messages.get(platform_key, {})
        lines.append(f"## {label}")

        if isinstance(msg, dict):
            subject = msg.get("subject")
            body = msg.get("body", "")
            if subject:
                lines.append(f"**Subject:** {subject}")
                lines.append("")
            if body:
                lines.append(body)
            else:
                lines.append("*[Message not generated — platform may be missing contact info]*")
        else:
            lines.append(str(msg) if msg else "*[Not generated]*")

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)
