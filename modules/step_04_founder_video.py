"""
modules/step_04_founder_video.py — Step 4: Founder Video

Generates video script, Streamyard checklist, and social posting plan.
"""
import json
from datetime import datetime
from typing import Tuple

from core.deal import Deal
from core.logger import get_logger
from agents.content_agent import ContentAgent
from config import OUTPUT_DIR

logger = get_logger(__name__)


def run(deal: Deal, config: dict) -> Tuple[Deal, dict]:
    """
    Step 4: Generate founder video script and supporting materials.
    """
    logger.info(f"[{deal.deal_id}] ▶ Step 4: Founder Video")

    errors = []
    human_actions = []
    outputs = {}

    output_dir = OUTPUT_DIR / deal.deal_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Check if founder declined video ──────────────────────────────────────
    if "04" in deal.skipped_steps:
        logger.info(f"[{deal.deal_id}] Step 4 marked as skipped (founder declined video)")
        deal.log_step("04", "skipped", "Founder declined video — step skipped.")
        return deal, {
            "success": True,
            "output": {"skipped": True, "reason": "Founder declined video"},
            "errors": [],
            "human_actions_required": [],
        }

    agent = ContentAgent()

    # ── Generate video script ─────────────────────────────────────────────────
    try:
        script_data = agent.generate_video_script(deal)
        script_path = output_dir / "founder_video_script.json"
        with open(script_path, "w") as f:
            json.dump(script_data, f, indent=2)

        # Write human-readable markdown
        md_path = output_dir / "founder_video_script.md"
        _write_script_md(script_data, md_path, deal)
        outputs["video_script"] = str(md_path)
        logger.info(f"[{deal.deal_id}] Video script saved → {md_path}")
    except Exception as e:
        errors.append(f"Video script generation failed: {e}")
        logger.error(f"[{deal.deal_id}] Video script error: {e}")

    # ── Check founder social presence ─────────────────────────────────────────
    social_flags = []
    if not deal.founder_linkedin:
        social_flags.append("Founder LinkedIn profile is missing — required for investor outreach.")
        human_actions.append("⚠️ Founder LinkedIn profile not provided — add to deal record.")
    # Twitter/X is not in the Deal model but we flag the concept
    social_flags.append(
        "Verify founder has an active X (Twitter) account — required for social posting plan."
    )

    # ── Generate Streamyard checklist ─────────────────────────────────────────
    streamyard_checklist = _generate_streamyard_checklist(deal)
    streamyard_path = output_dir / "streamyard_checklist.md"
    streamyard_path.write_text(streamyard_checklist)
    outputs["streamyard_checklist"] = str(streamyard_path)

    # ── Generate social posting plan ──────────────────────────────────────────
    social_plan = _generate_social_plan(deal)
    social_path = output_dir / "social_posting_plan.md"
    social_path.write_text(social_plan)
    outputs["social_posting_plan"] = str(social_path)

    # Human actions
    human_actions.extend([
        "Founder must record 170-second video using the script provided.",
        "Upload to Opus.Pro for editing and clip extraction.",
        "Post clips per social_posting_plan.md schedule.",
        *social_flags,
    ])

    deal.log_step("04", "completed", "Video script, Streamyard checklist, and social plan generated.", outputs)

    return deal, {
        "success": len(errors) == 0,
        "output": outputs,
        "errors": errors,
        "human_actions_required": human_actions,
    }


def _write_script_md(data: dict, path, deal: Deal) -> None:
    lines = [
        f"# Founder Video Script — {deal.company_name}",
        f"**Founder:** {deal.founder_name}",
        f"**Total Runtime:** {data.get('total_duration_seconds', 170)} seconds",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d')}",
        "",
        "---",
        "",
    ]
    for section in data.get("sections", []):
        lines.append(f"## {section.get('section', '')} ({section.get('duration_seconds', 0)}s)")
        lines.append("")
        lines.append(section.get("script", ""))
        if section.get("notes"):
            lines.append(f"\n*Director note: {section['notes']}*")
        lines.append("")
        lines.append("---")
        lines.append("")

    if data.get("full_script"):
        lines.append("## Full Script (read-through version)")
        lines.append("")
        lines.append(data["full_script"])

    path.write_text("\n".join(lines))


def _generate_streamyard_checklist(deal: Deal) -> str:
    return f"""# Streamyard Recording Session Checklist — {deal.company_name}

**Founder:** {deal.founder_name}
**Date:** [SCHEDULE DATE]

## Before Recording
- [ ] Test internet connection (minimum 10 Mbps upload)
- [ ] Plug in wired ethernet if available
- [ ] Set up ring light or ensure good front-facing lighting
- [ ] Use external microphone or headset (no built-in laptop mic)
- [ ] Clean, professional background (or use virtual background)
- [ ] Close all unnecessary tabs and apps
- [ ] Silence phone and notifications
- [ ] Do a 30-second test recording and review quality
- [ ] Have water nearby

## Streamyard Setup
- [ ] Create Streamyard account at streamyard.com
- [ ] Create a new "Recording" (not stream)
- [ ] Set resolution to 1080p
- [ ] Enable "Record locally" for backup
- [ ] Do audio/video check in Streamyard pre-lobby

## During Recording
- [ ] Record each section separately for easier editing
- [ ] Aim for 2-3 takes per section
- [ ] Keep script nearby but speak naturally — not reading
- [ ] Look at camera (not screen) when speaking

## After Recording
- [ ] Download raw recording from Streamyard
- [ ] Upload to Opus.Pro for AI editing (clips, captions, highlights)
- [ ] Send to video editor for final polish
- [ ] Export: Full video + 5-7 short clips (30-60 seconds each)
"""


def _generate_social_plan(deal: Deal) -> str:
    return f"""# Social Posting Plan — {deal.company_name} Founder Video

**Founder:** {deal.founder_name}
**Target:** Investors, founders, industry community

## Posting Schedule (Week 1 after video release)

| Day | Platform | Content | CTA |
|-----|----------|---------|-----|
| Monday | LinkedIn | Full 2-min founder video | "We're raising ${deal.raise_amount/1e6:.1f}M — here's why" |
| Monday | X (Twitter) | 60-second clip: Problem/Solution | Link to full video |
| Tuesday | LinkedIn | Clip: Market Opportunity | Share metrics |
| Wednesday | X | Clip: Team credentials | Tag advisors |
| Thursday | LinkedIn | Written post: key company stats | Drive to deck request |
| Friday | X + LinkedIn | Clip: Ask + ROI | "DM me for more info" |
| Saturday | Investor Groups | Post full video in relevant LinkedIn groups | Engagement CTA |

## Target LinkedIn Groups to Post In
- [ ] Venture Capital & Private Equity
- [ ] Angel Investors Network
- [ ] {deal.industry.title()} Entrepreneurs
- [ ] Startup Funding & Investors
- [ ] [Industry-specific groups — research 5 additional]

## Hashtags
\\#{deal.industry.replace(' ', '')} #VentureCapital #StartupFunding #Investors #Fundraising #{deal.company_name.replace(' ', '')}

## Notes
- Tag relevant investors in posts (with discretion)
- Respond to every comment within 24 hours
- Share post analytics to Millenia Ventures weekly
"""
