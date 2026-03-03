"""
modules/step_10_pr_visibility.py — Step 10: PR & Visibility

Top 10 podcasts, outreach emails, and press release.
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
    Step 10: Generate podcast outreach list and emails, plus press release draft.
    """
    logger.info(f"[{deal.deal_id}] ▶ Step 10: PR & Visibility")

    errors = []
    human_actions = []
    outputs = {}

    output_dir = OUTPUT_DIR / deal.deal_id
    output_dir.mkdir(parents=True, exist_ok=True)

    agent = ContentAgent()

    # ── Find top 10 podcasts ──────────────────────────────────────────────────
    try:
        podcasts = agent.find_podcasts(deal)
        podcast_path = output_dir / "podcast_outreach_list.json"
        with open(podcast_path, "w") as f:
            json.dump({
                "deal_id": deal.deal_id,
                "company": deal.company_name,
                "industry": deal.industry,
                "generated_at": datetime.utcnow().isoformat(),
                "podcasts": podcasts,
            }, f, indent=2)
        outputs["podcast_list"] = str(podcast_path)
        logger.info(f"[{deal.deal_id}] {len(podcasts)} podcasts found")
    except Exception as e:
        errors.append(f"Podcast search failed: {e}")
        logger.error(f"[{deal.deal_id}] Podcast search error: {e}")
        podcasts = []

    # ── Draft podcast outreach emails ─────────────────────────────────────────
    if podcasts:
        try:
            email_lines = [
                f"# Podcast Outreach Emails — {deal.company_name}",
                f"Generated: {datetime.utcnow().strftime('%Y-%m-%d')}",
                "",
                "---",
                "",
            ]
            for podcast in podcasts:
                podcast_name = podcast.get("name", "Unknown")
                try:
                    email = agent.draft_podcast_outreach(deal, podcast)
                    email_lines.extend([
                        f"## {podcast_name}",
                        f"**Host:** {podcast.get('host', 'N/A')}",
                        f"**Contact:** {podcast.get('email', 'N/A')}",
                        f"**Focus:** {podcast.get('focus', 'N/A')}",
                        "",
                        f"**Subject:** {email.get('subject', '')}",
                        "",
                        email.get("body", ""),
                        "",
                        "---",
                        "",
                    ])
                except Exception as e:
                    errors.append(f"Email draft failed for {podcast_name}: {e}")
                    logger.warning(f"[{deal.deal_id}] Podcast email error for {podcast_name}: {e}")

            emails_path = output_dir / "podcast_emails.md"
            emails_path.write_text("\n".join(email_lines))
            outputs["podcast_emails"] = str(emails_path)
        except Exception as e:
            errors.append(f"Podcast email drafting failed: {e}")
            logger.error(f"[{deal.deal_id}] Podcast email error: {e}")

    # ── Generate press release ────────────────────────────────────────────────
    try:
        press_release = agent.draft_press_release(deal)
        pr_path = output_dir / "press_release_draft.json"
        with open(pr_path, "w") as f:
            json.dump(press_release, f, indent=2)

        # Write human-readable version
        pr_md_path = output_dir / "press_release_draft.md"
        pr_md_path.write_text(press_release.get("full_text", "Press release generation failed."))

        outputs["press_release"] = str(pr_md_path)
        logger.info(f"[{deal.deal_id}] Press release drafted → {pr_md_path}")
    except Exception as e:
        errors.append(f"Press release generation failed: {e}")
        logger.error(f"[{deal.deal_id}] Press release error: {e}")

    human_actions.extend([
        "Founder must confirm podcast participation for each show contacted.",
        "Phil or Das to distribute press release to media outlets.",
        "Send podcast_emails.md to each podcast after founder confirms participation.",
        "If founder declines podcasts: log skip reason and continue pipeline.",
    ])

    deal.log_step("10", "completed", f"PR materials generated: {len(podcasts)} podcasts, press release drafted.", outputs)

    return deal, {
        "success": len(errors) == 0,
        "output": outputs,
        "errors": errors,
        "human_actions_required": human_actions,
    }
