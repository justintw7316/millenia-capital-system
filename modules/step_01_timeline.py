"""
modules/step_01_timeline.py — Step 1: Timeline & Metrics

Calculates 90-day funding deadline, generates weekly milestones and tracking structure.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple

from core.deal import Deal
from core.logger import get_logger
from config import (
    FUNDING_DEADLINE_DAYS,
    WEEKLY_OUTREACH_TARGET,
    MEETINGS_PER_WEEK_TARGET,
    COMMITMENTS_PER_MONTH_TARGET,
    OUTPUT_DIR,
)

logger = get_logger(__name__)


def run(deal: Deal, config: dict) -> Tuple[Deal, dict]:
    """
    Step 1: Generate 90-day timeline, weekly milestones, and metrics tracking structure.

    Args:
        deal: Current Deal object.
        config: Config dict (from config.py).

    Returns:
        Updated Deal and result dict with success, output, errors, human_actions_required.
    """
    logger.info(f"[{deal.deal_id}] ▶ Step 1: Timeline & Metrics")

    errors = []
    human_actions = []

    # ── Resolve start date ────────────────────────────────────────────────────
    if deal.created_at:
        try:
            start_date = datetime.strptime(deal.created_at, "%Y-%m-%d")
        except ValueError:
            start_date = datetime.utcnow()
            errors.append(
                f"created_at '{deal.created_at}' could not be parsed — using today's date."
            )
            logger.warning(f"[{deal.deal_id}] Invalid created_at format — defaulting to today")
    else:
        start_date = datetime.utcnow()
        errors.append("created_at not set — using today's date for timeline.")
        logger.warning(f"[{deal.deal_id}] created_at missing — defaulting to today")

    deadline = start_date + timedelta(days=FUNDING_DEADLINE_DAYS)

    # ── Build weekly milestones ───────────────────────────────────────────────
    weeks = []
    for week_num in range(1, 14):  # 13 weeks ≈ 90 days
        week_start = start_date + timedelta(weeks=week_num - 1)
        week_end = week_start + timedelta(days=6)
        week_target_outreach = WEEKLY_OUTREACH_TARGET
        week_target_meetings = MEETINGS_PER_WEEK_TARGET
        # Commitments are monthly — flag weeks 4, 8, 12
        commitment_checkpoint = week_num in (4, 8, 12)

        weeks.append({
            "week": week_num,
            "start_date": week_start.strftime("%Y-%m-%d"),
            "end_date": week_end.strftime("%Y-%m-%d"),
            "targets": {
                "investor_outreaches": week_target_outreach,
                "meetings": week_target_meetings,
                "commitments": COMMITMENTS_PER_MONTH_TARGET if commitment_checkpoint else 0,
            },
            "is_commitment_checkpoint": commitment_checkpoint,
            "actuals": {
                "investor_outreaches": 0,
                "meetings": 0,
                "commitments": 0,
                "commitments_value": 0,
            },
            "notes": "",
        })

    # ── Weekly metrics form fields ────────────────────────────────────────────
    metrics_form = {
        "week_number": None,
        "reporting_period": {"start": None, "end": None},
        "investor_outreaches_sent": 0,
        "investor_responses_received": 0,
        "response_rate_percent": 0.0,
        "meetings_scheduled": 0,
        "meetings_completed": 0,
        "meeting_conversion_percent": 0.0,
        "new_commitments": 0,
        "new_commitments_value": 0,
        "total_committed_to_date": 0,
        "percent_of_raise_completed": 0.0,
        "key_wins": [],
        "blockers": [],
        "next_week_priorities": [],
        "notes": "",
    }

    # ── Build timeline output ─────────────────────────────────────────────────
    timeline = {
        "deal_id": deal.deal_id,
        "company_name": deal.company_name,
        "raise_amount": deal.raise_amount,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "deadline_date": deadline.strftime("%Y-%m-%d"),
        "funding_deadline_days": FUNDING_DEADLINE_DAYS,
        "weekly_milestones": weeks,
        "metrics_form_template": metrics_form,
        "generated_at": datetime.utcnow().isoformat(),
    }

    # ── Save output ───────────────────────────────────────────────────────────
    output_dir = OUTPUT_DIR / deal.deal_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "timeline.json"

    with open(output_path, "w") as f:
        json.dump(timeline, f, indent=2)

    logger.info(f"[{deal.deal_id}] Timeline saved → {output_path}")

    # ── Update deal ───────────────────────────────────────────────────────────
    deal.log_step("01", "completed", f"Timeline generated. Deadline: {deadline.strftime('%Y-%m-%d')}", str(output_path))

    return deal, {
        "success": True,
        "output": timeline,
        "errors": errors,
        "human_actions_required": human_actions,
        "output_file": str(output_path),
    }
