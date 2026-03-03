"""
modules/step_08_followup_campaign.py — Step 8: Follow-Up Campaign

Generates 12-week follow-up schedule with per-platform messages.
Platform rotation: Wed=X, Thu=SMS/WhatsApp, Fri=Email, Sat=LinkedIn
"""
import json
from datetime import datetime, timedelta
from typing import Tuple

from core.deal import Deal
from core.logger import get_logger
from agents.campaign_agent import CampaignAgent
from config import OUTPUT_DIR

logger = get_logger(__name__)

PLATFORM_SCHEDULE = {
    "wednesday": "x_twitter",
    "thursday_sms": "sms",
    "thursday_whatsapp": "whatsapp",
    "friday": "email",
    "saturday": "linkedin",
}


def run(deal: Deal, config: dict) -> Tuple[Deal, dict]:
    """
    Step 8: Generate 12-week follow-up campaign with weekly messages per platform.
    """
    logger.info(f"[{deal.deal_id}] ▶ Step 8: Follow-Up Campaign (Week {deal.outreach_week})")

    errors = []
    human_actions = []
    outputs = {}

    output_dir = OUTPUT_DIR / deal.deal_id
    output_dir.mkdir(parents=True, exist_ok=True)
    followup_dir = output_dir / "followup_campaign"
    followup_dir.mkdir(exist_ok=True)

    # ── Load investor list ─────────────────────────────────────────────────────
    investor_list_path = output_dir / "investor_list.json"
    investors = []
    if investor_list_path.exists():
        with open(investor_list_path) as f:
            investors = json.load(f).get("investors", [])

    if not investors:
        msg = "No investors found — run Step 7a first."
        errors.append(msg)
        deal.log_step("08", "failed", msg)
        return deal, {
            "success": False,
            "output": {},
            "errors": [msg],
            "human_actions_required": [],
        }

    # Filter: remove responded/opted-out investors from active follow-up
    responded_emails = {inv.get("email", "").lower() for inv in deal.investors_responded}
    opted_out = set()  # Would be populated from CRM in real system
    active_investors = [
        inv for inv in investors
        if inv.get("email", "").lower() not in responded_emails
        and inv.get("email", "").lower() not in opted_out
    ]

    logger.info(
        f"[{deal.deal_id}] Active follow-up targets: {len(active_investors)} "
        f"(removed {len(investors) - len(active_investors)} responded/opted-out)"
    )

    campaign_agent = CampaignAgent()

    # ── Generate 12-week schedule ─────────────────────────────────────────────
    schedule = _build_schedule(deal)
    schedule_path = output_dir / "followup_schedule.json"
    with open(schedule_path, "w") as f:
        json.dump(schedule, f, indent=2)
    outputs["followup_schedule"] = str(schedule_path)

    # ── Generate per-week message files ──────────────────────────────────────
    # Generate messages for current week + next 11 (full 12-week set)
    for week_num in range(1, 13):
        week_outputs = {}

        # Only generate full per-investor messages for current week
        # Future weeks get template messages (too expensive to generate all at once)
        if week_num == 1 and active_investors:
            investor_messages = []
            for investor in active_investors[:5]:  # First 5 for demo; real system does all
                try:
                    messages = campaign_agent.generate_followup_sequence(deal, investor, week_num)
                    investor_messages.append(messages)
                except Exception as e:
                    errors.append(f"Follow-up gen failed for {investor.get('full_name')}: {e}")
                    logger.warning(f"[{deal.deal_id}] Follow-up error week {week_num}: {e}")

            week_path = followup_dir / f"week_{week_num:02d}_messages.json"
            with open(week_path, "w") as f:
                json.dump({"week": week_num, "investor_messages": investor_messages}, f, indent=2)
            week_outputs["messages_file"] = str(week_path)

        # Generate week markdown summary
        week_md = _generate_week_md(deal, week_num, schedule)
        week_md_path = followup_dir / f"week_{week_num:02d}_messages.md"
        week_md_path.write_text(week_md)
        week_outputs["md_file"] = str(week_md_path)
        outputs[f"week_{week_num:02d}"] = week_outputs

    deal.outreach_week += 1
    logger.info(
        f"[{deal.deal_id}] 12-week follow-up schedule generated. "
        f"Outreach week advanced to {deal.outreach_week}"
    )

    deal.log_step("08", "completed", f"12-week follow-up campaign generated. Outreach week: {deal.outreach_week}", outputs)

    return deal, {
        "success": len(errors) == 0,
        "output": outputs,
        "errors": errors,
        "human_actions_required": human_actions,
    }


def _build_schedule(deal: Deal) -> dict:
    """Build the 12-week sending schedule."""
    start = datetime.utcnow()
    weeks = []
    for week_num in range(1, 13):
        week_start = start + timedelta(weeks=week_num - 1)
        # Calculate send dates for each platform
        send_dates = {
            "x_twitter": (week_start + timedelta(days=_weekday_offset(week_start, 2))).strftime("%Y-%m-%d"),  # Wednesday
            "sms": (week_start + timedelta(days=_weekday_offset(week_start, 3))).strftime("%Y-%m-%d"),        # Thursday
            "whatsapp": (week_start + timedelta(days=_weekday_offset(week_start, 3))).strftime("%Y-%m-%d"),   # Thursday
            "email": (week_start + timedelta(days=_weekday_offset(week_start, 4))).strftime("%Y-%m-%d"),      # Friday
            "linkedin": (week_start + timedelta(days=_weekday_offset(week_start, 5))).strftime("%Y-%m-%d"),   # Saturday
        }
        weeks.append({
            "week": week_num,
            "week_start": week_start.strftime("%Y-%m-%d"),
            "send_dates": send_dates,
            "platforms": list(PLATFORM_SCHEDULE.values()),
        })
    return {
        "deal_id": deal.deal_id,
        "company_name": deal.company_name,
        "generated_at": start.isoformat(),
        "total_weeks": 12,
        "platform_rotation": PLATFORM_SCHEDULE,
        "weeks": weeks,
    }


def _weekday_offset(from_date: datetime, target_weekday: int) -> int:
    """Return days to add to reach target_weekday (0=Mon, 6=Sun)."""
    current = from_date.weekday()
    delta = (target_weekday - current) % 7
    return delta


def _generate_week_md(deal: Deal, week_num: int, schedule: dict) -> str:
    week_data = next((w for w in schedule.get("weeks", []) if w["week"] == week_num), {})
    send_dates = week_data.get("send_dates", {})

    lines = [
        f"# Week {week_num} Follow-Up Messages — {deal.company_name}",
        f"**Week Start:** {week_data.get('week_start', 'N/A')}",
        "",
        "## Platform Send Schedule",
        "",
        f"| Platform | Send Date | Message Type |",
        f"|----------|-----------|--------------|",
        f"| X (Twitter) | {send_dates.get('x_twitter', 'N/A')} | Week {week_num} update |",
        f"| SMS | {send_dates.get('sms', 'N/A')} | Week {week_num} update |",
        f"| WhatsApp | {send_dates.get('whatsapp', 'N/A')} | Week {week_num} update |",
        f"| Email | {send_dates.get('email', 'N/A')} | Week {week_num} update |",
        f"| LinkedIn | {send_dates.get('linkedin', 'N/A')} | Week {week_num} update |",
        "",
        "## Message Templates",
        "",
        f"### X (Twitter) — Wednesday",
        f"Week {week_num} update: [Add 1 specific milestone]. {deal.company_name} is [making progress on X]. "
        f"Interested in learning more? DM me.",
        "",
        f"### SMS — Thursday",
        f"Hi [Name], {deal.company_name} week {week_num} update: [milestone]. Worth a quick call? — {deal.founder_name}",
        "",
        f"### WhatsApp — Thursday",
        f"Hi [Name], following up on {deal.company_name}. This week: [milestone]. "
        f"Would love to schedule a 15-min call. Are you available this week?",
        "",
        f"### Email — Friday",
        f"**Subject:** Week {week_num} — {deal.company_name} Update",
        f"",
        f"Hi [Name],",
        f"",
        f"Quick week {week_num} update on {deal.company_name}:",
        f"",
        f"- [Milestone 1]",
        f"- [Milestone 2]",
        f"- [Traction metric]",
        f"",
        f"We're raising ${deal.raise_amount:,.0f} and making strong progress. "
        f"Would you have 20 minutes this week?",
        f"",
        f"Best,",
        f"{deal.founder_name}",
        "",
        f"### LinkedIn — Saturday",
        f"**Subject:** Week {week_num} Progress Update — {deal.company_name}",
        f"",
        f"Hi [Name], sharing a quick update: [milestone]. Still raising ${deal.raise_amount:,.0f}. "
        f"Would love to connect for 20 minutes.",
        "",
        "## Instructions",
        "- Personalize [Name], [Milestone 1], [Milestone 2] for each investor",
        "- Remove any investors who respond (they enter the meeting funnel)",
        "- Immediately blacklist any investor who opts out — do not re-contact",
        "- After 3 weeks of no response: move to cold list",
    ]
    return "\n".join(lines)
