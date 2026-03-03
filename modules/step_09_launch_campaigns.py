"""
modules/step_09_launch_campaigns.py — Step 9: Launch Campaigns

MeetAlfred launch notification, Alignable setup, investor group list, broker-dealer portal if $5M+.
"""
from datetime import datetime
from typing import Tuple

from core.deal import Deal
from core.logger import get_logger
from config import OUTPUT_DIR, BROKER_DEALER_THRESHOLD

logger = get_logger(__name__)


def run(deal: Deal, config: dict) -> Tuple[Deal, dict]:
    """
    Step 9: Generate campaign launch materials and platform setup guides.
    """
    logger.info(f"[{deal.deal_id}] ▶ Step 9: Launch Campaigns")

    errors = []
    human_actions = []
    outputs = {}

    output_dir = OUTPUT_DIR / deal.deal_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Campaign launch checklist ─────────────────────────────────────────────
    launch_checklist = _generate_launch_checklist(deal)
    checklist_path = output_dir / "campaign_launch_checklist.md"
    checklist_path.write_text(launch_checklist)
    outputs["launch_checklist"] = str(checklist_path)

    # ── Alignable setup guide ─────────────────────────────────────────────────
    alignable_guide = _generate_alignable_guide(deal)
    alignable_path = output_dir / "alignable_setup_guide.md"
    alignable_path.write_text(alignable_guide)
    outputs["alignable_guide"] = str(alignable_path)

    # ── Broker-dealer portal checklist if $5M+ ────────────────────────────────
    if deal.raise_amount >= BROKER_DEALER_THRESHOLD:
        broker_checklist = _generate_broker_dealer_checklist(deal)
        broker_path = output_dir / "broker_dealer_checklist.md"
        broker_path.write_text(broker_checklist)
        outputs["broker_dealer_checklist"] = str(broker_path)
        human_actions.append(
            f"⚠️ PHIL REQUIRED: Raise is ${deal.raise_amount:,.0f} (≥ $5M) — "
            f"broker-dealer portal submission required. See broker_dealer_checklist.md."
        )
        logger.info(f"[{deal.deal_id}] Broker-dealer checklist generated (raise ≥ $5M)")

    human_actions.extend([
        "Das: Launch MeetAlfred campaign after Phil approval (see Step 7c).",
        "Set up Alignable account per alignable_setup_guide.md.",
        "Join LinkedIn, Facebook, and Alignable investor groups listed in the guide.",
    ])

    deal.campaign_active = True
    deal.log_step("09", "completed", "Campaign launch materials generated.", outputs)

    return deal, {
        "success": True,
        "output": outputs,
        "errors": errors,
        "human_actions_required": human_actions,
    }


def _generate_launch_checklist(deal: Deal) -> str:
    return f"""# Campaign Launch Checklist — {deal.company_name}

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d')}

## Pre-Launch (Phil & Das)
- [ ] Phil approves MeetAlfred campaign draft (meetalfred_campaign_draft.json)
- [ ] Phil approves investor list (investor_list.json)
- [ ] A/B test variant selected (ab_test_variants.md)
- [ ] All outreach messages reviewed (outreach_bundle.json)

## MeetAlfred Launch (Das)
- [ ] Log into MeetAlfred account
- [ ] Import meetalfred_campaign_draft.json
- [ ] Upload investor contact list
- [ ] Set sending window: Mon–Fri, 8am–5pm investor's local timezone
- [ ] Set daily send limit: 20-25 connections/day (stay within LinkedIn limits)
- [ ] Set follow-up delays per sequence (3 days, 7 days)
- [ ] Enable reply detection (auto-pause follow-ups on reply)
- [ ] Launch campaign and confirm with Phil

## Das — Notification Email to Send
**To:** Phil
**Subject:** MeetAlfred Campaign Launched — {deal.company_name}

Hi Phil, the {deal.company_name} investor outreach campaign is now live on MeetAlfred.

- Target investors: [Count from investor list]
- Campaign ID: {deal.meetalfred_campaign_id or '[To be set after launch]'}
- A/B variant selected: [A/B]
- Expected connection requests per day: 20-25
- First follow-up: 3 days after connection
- Second follow-up: 7 days after first message

I'll report stats weekly.

Best, Das

## Ongoing Monitoring
- [ ] Weekly: Check MeetAlfred dashboard stats
- [ ] Weekly: Export reply list and add to CRM
- [ ] Weekly: Remove responded investors from sequence
- [ ] Weekly: Report to Phil (see Step 14: Reporting)
"""


def _generate_alignable_guide(deal: Deal) -> str:
    return f"""# Alignable Account Setup Guide — {deal.company_name}

**Alignable:** Business networking platform with strong SMB and investor community.
**URL:** https://www.alignable.com/

## Account Setup Steps
1. Go to alignable.com and create a business account
2. Business name: {deal.company_name}
3. Upload company logo and complete all profile fields
4. Add company description (use tear sheet overview)
5. Link to company website: {deal.company_website}
6. Add industry: {deal.industry}

## Profile Optimization
- [ ] Complete 100% of profile fields
- [ ] Add 3-5 services/products
- [ ] Upload photos (team, product, office)
- [ ] Set location to HQ city
- [ ] Add at least 3 recommendations

## Investor Groups to Join on Alignable
- [ ] Investor Network
- [ ] Startup Founders & Investors
- [ ] Angel Investors
- [ ] {deal.industry.title()} Business Network
- [ ] Local business network (by city)

## LinkedIn Investor Groups to Join
- [ ] Venture Capital & Private Equity Network
- [ ] Angel Investor Network
- [ ] Startup Funding & Investors
- [ ] {deal.industry.title()} Entrepreneurs
- [ ] TechCrunch Startup Network

## Facebook Groups to Join
- [ ] Venture Capital Investment Opportunities
- [ ] Angel Investors Group
- [ ] Startup Funding Network
- [ ] {deal.industry.title()} Startups & Investors

## Message Template for Alignable Connections

Hi [Name], I noticed you're active in the investor community on Alignable.
I'm {deal.founder_name}, founder of {deal.company_name} — a {deal.industry} company
raising ${deal.raise_amount:,.0f}. Would love to connect and share what we're building.

---

## Weekly Alignable Activity
- Connect with 10-15 new investors per week
- Engage with 3-5 posts in investor groups per week
- Post a company update every 2 weeks
"""


def _generate_broker_dealer_checklist(deal: Deal) -> str:
    return f"""# Broker-Dealer Portal Submission Checklist
## ⚠️ PHIL REQUIRED — Raise ≥ $5M

**Company:** {deal.company_name}
**Raise Amount:** ${deal.raise_amount:,.0f}
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d')}

This deal exceeds $5M and requires engagement with registered broker-dealer portal(s).
**Phil must handle all broker-dealer coordination.**

## Broker-Dealer Portals to Submit To
- [ ] DealMaker (https://www.dealmaker.tech/)
- [ ] Netcapital (https://netcapital.com/)
- [ ] Republic (https://republic.com/)
- [ ] StartEngine (https://www.startengine.com/)
- [ ] Wefunder (https://wefunder.com/)
- [ ] SeedInvest (https://www.seedinvest.com/)

## Required Documents for Submission
- [ ] Pitch deck (approved version)
- [ ] PPM (Private Placement Memorandum)
- [ ] Subscription Agreement
- [ ] Financial projections (3-5 year)
- [ ] Use of funds
- [ ] Cap table (current)
- [ ] Corporate formation documents
- [ ] Founder background (bio, LinkedIn)

## Compliance Requirements
- [ ] Confirm Regulation D exemption (506b or 506c)
- [ ] Confirm accredited investor verification method
- [ ] Confirm FINRA broker-dealer registration requirements
- [ ] Legal review by Dock Walls before submission

## Phil Action Items
1. Select appropriate portal(s) based on deal structure
2. Coordinate with Dock Walls for legal review
3. Submit deal to portal(s)
4. Monitor portal application status
5. Report portal responses to Millenia Ventures team

## Notes
- Broker-dealer portal fees typically: 5-8% of raise
- Timeline: 2-4 weeks for portal approval/rejection
- Do NOT proceed with portal submission without Dock Walls sign-off
"""
