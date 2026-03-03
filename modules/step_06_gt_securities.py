"""
modules/step_06_gt_securities.py — Step 6: GT Securities

Human-only step. Generates a notification for Philip with deal details.
Do NOT attempt to automate outreach here.
"""
from datetime import datetime
from typing import Tuple

from core.deal import Deal
from core.logger import get_logger
from config import OUTPUT_DIR

logger = get_logger(__name__)


def run(deal: Deal, config: dict) -> Tuple[Deal, dict]:
    """
    Step 6: Generate GT Securities notification for Philip.

    THIS STEP IS HUMAN-ONLY. Philip handles all GT Securities coordination.
    This module only generates the notification — it does NOT send it.
    """
    logger.info(f"[{deal.deal_id}] ▶ Step 6: GT Securities — Generating Philip notification")

    output_dir = OUTPUT_DIR / deal.deal_id
    output_dir.mkdir(parents=True, exist_ok=True)

    notification = _generate_philip_notification(deal)
    notification_path = output_dir / "philip_notification.md"
    notification_path.write_text(notification)

    logger.info(f"[{deal.deal_id}] Philip notification saved → {notification_path}")

    deal.log_step("06", "completed", "GT Securities notification generated for Philip.", str(notification_path))

    return deal, {
        "success": True,
        "output": {"philip_notification": str(notification_path)},
        "errors": [],
        "human_actions_required": [
            "Philip: Review philip_notification.md and coordinate GT Securities engagement for this deal.",
            "Philip: Confirm GT Securities involvement before Step 12 (Traditional Outreach).",
        ],
    }


def _generate_philip_notification(deal: Deal) -> str:
    return f"""# GT Securities — Deal Notification for Philip

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
**Action Required By:** Philip

---

## Deal Summary

| Field | Value |
|-------|-------|
| Deal ID | {deal.deal_id} |
| Company | {deal.company_name} |
| Website | {deal.company_website} |
| Industry | {deal.industry} |
| Raise Amount | ${deal.raise_amount:,.0f} |
| Current Stage | {deal.stage.value} |

## Founder Information

| Field | Value |
|-------|-------|
| Name | {deal.founder_name} |
| Email | {deal.founder_email} |
| LinkedIn | {deal.founder_linkedin} |

## Document Status

| Document | Status |
|----------|--------|
| Tear Sheet | {deal.documents.tear_sheet.value} |
| Pitch Deck | {deal.documents.pitch_deck.value} |
| Financial Projections | {deal.documents.financial_projections.value} |
| NDA | {deal.documents.nda.value} |
| PPM | {deal.documents.ppm.value} |
| Subscription Agreement | {deal.documents.subscription_agreement.value} |
| Wiring Instructions | {deal.documents.wiring_instructions.value} |
| Use of Funds | {deal.documents.use_of_funds.value} |

## Required Action (Philip)

This deal has entered the pipeline and requires your GT Securities review and coordination. Specifically:

1. **Review deal structure** — Confirm raise amount, instrument type, and deal terms are aligned with GT Securities standards.
2. **Identify GT Securities contacts** — Flag any current GT Securities colleagues who may have relevant investor relationships for this deal.
3. **Coordinate network access** — Determine if GT Securities network should be engaged for this raise (see Step 12: Traditional Outreach).
4. **Compliance check** — Confirm deal structure is compliant with relevant securities regulations.
{"5. **Broker-dealer portal** — Raise is $5M+ — initiate broker-dealer portal submission process." if deal.raise_amount >= 5_000_000 else ""}

## Notes

- This step is handled exclusively by Philip — no automated outreach will be initiated.
- Next automated step: Step 7a (Investor Discovery) will proceed in parallel.
- If GT Securities introduces any investor contacts, add them to investor_contacts_enriched.csv.

---
*System generated — Millenia Ventures Capital Formation Automation*
"""
