"""
modules/step_12_traditional_outreach.py — Step 12: Traditional Outreach

Warm market checklist and GT Securities colleague outreach template.
This step is largely human-executed.
"""
from datetime import datetime
from typing import Tuple

from core.deal import Deal
from core.logger import get_logger
from config import OUTPUT_DIR

logger = get_logger(__name__)


def run(deal: Deal, config: dict) -> Tuple[Deal, dict]:
    """
    Step 12: Generate warm market outreach checklist and GT Securities colleague template.
    All outreach in this step is human-executed.
    """
    logger.info(f"[{deal.deal_id}] ▶ Step 12: Traditional Outreach")

    output_dir = OUTPUT_DIR / deal.deal_id
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {}

    # ── Warm market checklist ─────────────────────────────────────────────────
    warm_market = _generate_warm_market_checklist(deal)
    warm_path = output_dir / "warm_market_checklist.md"
    warm_path.write_text(warm_market)
    outputs["warm_market_checklist"] = str(warm_path)

    # ── GT Securities outreach template ──────────────────────────────────────
    gt_template = _generate_gt_securities_template(deal)
    gt_path = output_dir / "gt_securities_outreach_template.md"
    gt_path.write_text(gt_template)
    outputs["gt_securities_template"] = str(gt_path)

    human_actions = [
        "Phil/Das: Work through warm_market_checklist.md — all outreach is human-executed.",
        "Phil: Coordinate GT Securities colleague outreach via gt_securities_outreach_template.md.",
        "Track all contacts in the checklist tracking fields.",
        "Report warm market outreach results in weekly Step 14 report.",
    ]

    deal.log_step("12", "completed", "Warm market and GT Securities outreach materials generated.", outputs)

    return deal, {
        "success": True,
        "output": outputs,
        "errors": [],
        "human_actions_required": human_actions,
    }


def _generate_warm_market_checklist(deal: Deal) -> str:
    return f"""# Warm Market Outreach Checklist — {deal.company_name}

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d')}
**All outreach in this section is human-executed.**

---

## Millenia Ventures Network

### Tier 1 — High-Priority Contacts (Personal Relationships)
Work through your immediate network first. These contacts have the highest conversion rate.

| Contact Name | Relationship | Email/Phone | Contacted | Response | Notes |
|-------------|-------------|-------------|-----------|----------|-------|
| | | | [ ] | | |
| | | | [ ] | | |
| | | | [ ] | | |
| | | | [ ] | | |
| | | | [ ] | | |

### Tier 2 — Secondary Network (2nd-Degree Connections)
Ask Tier 1 contacts for introductions to these individuals.

| Contact Name | Introduced By | Email/Phone | Contacted | Response | Notes |
|-------------|--------------|-------------|-----------|----------|-------|
| | | | [ ] | | |
| | | | [ ] | | |
| | | | [ ] | | |
| | | | [ ] | | |
| | | | [ ] | | |

## Outreach Email Template (Warm Market)

**Subject:** Investment Opportunity — {deal.company_name} (Intro from [Mutual Contact])

Hi [First Name],

I hope you're doing well. I'm reaching out because I think you'd be a great fit for an investment opportunity we're working on.

**The company:** {deal.company_name} — a {deal.industry} company raising ${deal.raise_amount:,.0f}.

**Why I thought of you:**
- [Specific reason based on your relationship]
- [Connection to their investment focus or background]

I'd love to share more details. This opportunity is available to accredited investors. Would you have 15 minutes for a quick call this week?

Best,
[Your name]

---

## Outreach Script (Phone/In-Person)

"Hey [Name], I wanted to reach out about an exciting investment opportunity I'm involved with. A company called {deal.company_name} — they're in {deal.industry} and raising ${deal.raise_amount/1e6:.1f}M. Given your background in [X], I immediately thought of you. Do you have a few minutes to chat about it?"

---

## Tracking Rules
- Mark each contact as contacted on the date outreach is made
- Log response type: Interested / Not Interested / Follow Up / No Response
- Add all interested contacts to investor_list.json with source = "warm_market"
- Do not send pitch deck without completing Step 11 vetting checklist
"""


def _generate_gt_securities_template(deal: Deal) -> str:
    return f"""# GT Securities Colleague Outreach Template — {deal.company_name}

**Coordinated by:** Philip
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d')}

---

## Overview
Reach out to relevant GT Securities colleagues who may have accredited investor contacts
interested in {deal.industry} investments at the ${deal.raise_amount/1e6:.1f}M raise level.

## Colleague Outreach Email

**Subject:** Investment Opportunity for Your Network — {deal.company_name}

Hi [Colleague Name],

I hope you're doing well. I'm working with a client, {deal.company_name}, that I think could be
a strong fit for some of the accredited investors in your network.

**Quick overview:**
- **Company:** {deal.company_name} | {deal.industry.title()}
- **Raising:** ${deal.raise_amount:,.0f}
- **Stage:** Seed/Early Growth
- **Website:** {deal.company_website}

The company has strong fundamentals and a compelling team. I'd be happy to share the full deck
and connect you with the founder if you see potential interest in your network.

Would you be open to a quick 10-minute call this week to see if there's a fit?

Thanks,
Philip
[Contact info]

---

## GT Securities Colleague Tracking

| Colleague Name | Branch/Location | Contacted Date | Response | Referrals Given | Notes |
|---------------|----------------|----------------|----------|-----------------|-------|
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |

## Follow-Up Rules
- Wait 3 business days for response before follow-up
- Maximum 2 follow-up attempts per colleague
- Log all referrals in investor_list.json with source = "gt_securities"
- All referrals must complete Step 11 vetting before receiving deal documents

## Compliance Note
All GT Securities outreach must comply with firm policies on private investment sharing.
Confirm with compliance before distributing deal materials through GT Securities channels.
"""
