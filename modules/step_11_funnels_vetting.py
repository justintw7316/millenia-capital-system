"""
modules/step_11_funnels_vetting.py — Step 11: Funnels & Investor Vetting

Facebook ad brief, webinar template, investor vetting forms.
"""
from datetime import datetime
from typing import Tuple

from core.deal import Deal
from core.logger import get_logger
from config import OUTPUT_DIR

logger = get_logger(__name__)


def run(deal: Deal, config: dict) -> Tuple[Deal, dict]:
    """
    Step 11: Generate funnel materials, investor vetting forms, and Calendly setup.
    """
    logger.info(f"[{deal.deal_id}] ▶ Step 11: Funnels & Investor Vetting")

    errors = []
    human_actions = []
    outputs = {}

    output_dir = OUTPUT_DIR / deal.deal_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Facebook ad brief ─────────────────────────────────────────────────────
    fb_brief = _generate_facebook_ad_brief(deal)
    fb_path = output_dir / "facebook_ad_brief.md"
    fb_path.write_text(fb_brief)
    outputs["facebook_ad_brief"] = str(fb_path)

    # ── Webinar invite template ───────────────────────────────────────────────
    webinar = _generate_webinar_invite(deal)
    webinar_path = output_dir / "webinar_invite_template.md"
    webinar_path.write_text(webinar)
    outputs["webinar_invite"] = str(webinar_path)

    # ── Investor vetting questionnaire ────────────────────────────────────────
    vetting_form = _generate_vetting_form(deal)
    vetting_path = output_dir / "investor_vetting_form.md"
    vetting_path.write_text(vetting_form)
    outputs["investor_vetting_form"] = str(vetting_path)

    # ── Pre-meeting vetting checklist ─────────────────────────────────────────
    premeet_checklist = _generate_premeet_checklist(deal)
    premeet_path = output_dir / "pre_meeting_vetting_checklist.md"
    premeet_path.write_text(premeet_checklist)
    outputs["pre_meeting_checklist"] = str(premeet_path)

    human_actions.extend([
        "Indian/Sacramento team: Build Facebook funnels and ads per facebook_ad_brief.md.",
        "Set up Calendly booking link and integrate with investor vetting form.",
        "If unaccredited investor detected during vetting: send auto-disqualification email (template in vetting form).",
        "Schedule webinar and send webinar_invite_template.md to investor list.",
    ])

    deal.log_step("11", "completed", "Funnel materials and vetting forms generated.", outputs)

    return deal, {
        "success": True,
        "output": outputs,
        "errors": errors,
        "human_actions_required": human_actions,
    }


def _generate_facebook_ad_brief(deal: Deal) -> str:
    return f"""# Facebook Ad Brief — {deal.company_name}

**Prepared for:** Indian/Sacramento Marketing Team
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d')}

---

## Campaign Objective
Generate qualified investor leads for {deal.company_name}'s ${deal.raise_amount/1e6:.1f}M raise.

## Target Audience

### Primary Audience
- **Age:** 35-65
- **Income:** $200,000+ (proxy for accredited investor status)
- **Net worth interests:** Investing, private equity, venture capital
- **Interests:** Startup investing, angel investing, entrepreneurship, {deal.industry}
- **Location:** United States (focus: CA, NY, TX, FL, WA)
- **Job titles:** Founder, CEO, Managing Partner, General Partner, Director, VP Finance

### Secondary Audience (Lookalike)
- Lookalike of email list of existing Millenia Ventures investor contacts
- 1% lookalike in United States

## Ad Formats
1. **Lead Generation Ad** (primary) — "Learn about this investment opportunity"
2. **Video Ad** — Use founder video clip (30-60 seconds)
3. **Carousel Ad** — Company highlights with 3-5 data points

## Ad Copy Templates

### Headline Options
- "A {deal.industry} company raising ${deal.raise_amount/1e6:.1f}M — Are you the right investor?"
- "Accredited investors: {deal.company_name} is raising ${deal.raise_amount/1e6:.1f}M"
- "Investment opportunity in {deal.industry} — Limited spots available"

### Body Copy
{deal.company_name} is building the future of {deal.industry}. We're raising ${deal.raise_amount:,.0f} from accredited investors.

✓ Industry: {deal.industry.title()}
✓ Raising: ${deal.raise_amount/1e6:.1f}M
✓ Stage: Early growth
✓ Strong team with domain expertise

[Learn More] — leads to investor vetting questionnaire

### Disqualification Copy (for thank-you page after non-accredited submission)
"Thank you for your interest. This opportunity is only available to SEC-accredited investors. We'll keep you informed of future opportunities that may be a fit."

## Budget Recommendation
- Test budget: $500/week for 2 weeks
- Scale to: $2,000/week if CPL < $50
- Target CPL (Cost per Lead): < $30
- Target qualified lead rate: > 20%

## Funnel Flow
Facebook Ad → Lead Form → Calendly Booking → Pre-Meeting Vetting Call → Pitch Deck Distribution

## Tracking
- Install Facebook Pixel on landing page
- Set conversion event: Lead form submission
- Set custom event: Calendly booking completed
- Report weekly to Millenia Ventures team
"""


def _generate_webinar_invite(deal: Deal) -> str:
    return f"""# Webinar Invite Template — {deal.company_name} Investor Briefing

**Subject:** [INVITE] {deal.company_name} Investor Briefing — ${deal.raise_amount/1e6:.1f}M Round

---

Hi [First Name],

You're invited to an exclusive investor briefing for **{deal.company_name}**, a {deal.industry} company currently raising ${deal.raise_amount:,.0f}.

## What You'll Learn

- The specific problem {deal.company_name} solves and why now is the right time
- Market opportunity and growth trajectory
- Business model and path to profitability
- Team background and competitive advantages
- Investment terms and how to participate

## Event Details

- **Format:** Live webinar (Zoom)
- **Date:** [INSERT DATE]
- **Time:** [INSERT TIME] [TIMEZONE]
- **Duration:** 45 minutes + Q&A
- **Presenter:** {deal.founder_name}, Founder & CEO

## Reserve Your Spot

[CALENDLY BOOKING LINK]

*Space is limited to qualified accredited investors. A brief pre-registration form is required.*

## This Opportunity in Brief

| | |
|--|--|
| Company | {deal.company_name} |
| Industry | {deal.industry.title()} |
| Raise | ${deal.raise_amount:,.0f} |
| Stage | Seed / Early Growth |
| Website | {deal.company_website} |

Questions? Reply to this email or contact Millenia Ventures directly.

Best regards,
Millenia Ventures Capital Formation Team

---
*This communication is for informational purposes only and does not constitute an offer to sell or solicitation to buy securities. This opportunity is limited to accredited investors as defined by the SEC.*
"""


def _generate_vetting_form(deal: Deal) -> str:
    return f"""# Investor Vetting Questionnaire — {deal.company_name}

**Purpose:** Pre-qualify investors before sharing deal documents.

---

## Form Fields (Typeform / JotForm / Google Form)

### Section 1: Contact Information
1. First Name *
2. Last Name *
3. Email Address *
4. Phone Number
5. LinkedIn Profile URL

### Section 2: Accreditation Status

**Question:** Are you an accredited investor as defined by the SEC?
*(An accredited investor has individual income over $200K/year, or $300K with spouse, in each of the last 2 years; OR a net worth exceeding $1M excluding primary residence; OR holds Series 7, 65, or 82 license)*

- [ ] Yes, I am an accredited investor
- [ ] No, I am not an accredited investor
- [ ] I am unsure — I'd like to learn more

*If "No" selected → Trigger disqualification email (see below)*

### Section 3: Investment Experience
6. How many private investments have you made in the past 5 years?
   - 0 | 1-2 | 3-5 | 6-10 | 10+
7. What is your typical investment check size?
   - Under $10K | $10K-$50K | $50K-$250K | $250K-$1M | Over $1M
8. What sectors do you typically invest in? (multi-select)
   - Technology | Healthcare | Real Estate | Consumer | {deal.industry.title()} | Other

### Section 4: Interest Level
9. How did you hear about {deal.company_name}?
10. What specifically interests you about this opportunity?
11. Are you ready to invest in the next 90 days? Yes / No / Maybe

### Section 5: Scheduling
12. Would you like to schedule a 20-minute introductory call?
    [CALENDLY LINK]

---

## Calendly Integration Instructions
1. Create Calendly event: "Investor Intro Call — {deal.company_name}"
2. Duration: 20 minutes
3. Buffer: 10 minutes between meetings
4. Confirmation email: Send investor_vetting_form link before call
5. Reminder: Send 24 hours and 1 hour before call

---

## Disqualification Email Template
**Trigger:** Respondent selects "No" to accreditation question.

**Subject:** Thank You for Your Interest in {deal.company_name}

Hi [First Name],

Thank you for your interest in {deal.company_name}.

This particular investment opportunity is structured under SEC Regulation D and is currently available only to accredited investors. Based on your response, you may not currently qualify under SEC guidelines.

We appreciate your enthusiasm and will keep you informed as new opportunities arise that may be a better fit.

If you believe this was an error or would like to understand accredited investor requirements better, please reply to this email.

Best regards,
Millenia Ventures Team

---

## Pre-Meeting Vetting Checklist
*Complete before sharing pitch deck with any investor.*
- [ ] Accredited investor status confirmed (Yes on form)
- [ ] NDA signed and approved
- [ ] LinkedIn profile verified (real person, professional background)
- [ ] Investment check size compatible with deal terms
- [ ] No red flags in background (Google search + LinkedIn review)
- [ ] Calendly call completed or scheduled
"""


def _generate_premeet_checklist(deal: Deal) -> str:
    return f"""# Pre-Meeting Vetting Checklist — {deal.company_name}

Complete ALL items before sharing pitch deck or scheduling a founder call.

## Step 1: Identity Verification
- [ ] Investor submitted vetting questionnaire
- [ ] LinkedIn profile verified (real, current, professional)
- [ ] Google search for investor name + firm (no red flags)
- [ ] Email address is professional (not free Gmail/Yahoo for institutional investors)

## Step 2: Accreditation
- [ ] Investor confirmed accredited status on vetting form
- [ ] If uncertain: provide SEC accreditation definition and request confirmation
- [ ] NDA signed (see NDA tracking document)

## Step 3: Fit Assessment
- [ ] Check size compatible: target ${deal.raise_amount * 0.005:,.0f} – ${deal.raise_amount * 0.05:,.0f} per investor
- [ ] Industry interest matches: {deal.industry}
- [ ] Timeline compatible: investor can decide within 90 days

## Step 4: CRM Entry
- [ ] Add investor to investor_list.json with status = "vetting_passed"
- [ ] Log interaction in step_log
- [ ] Assign to follow-up sequence

## If All Items Pass → Proceed to:
1. Send pitch deck via secure Box link
2. Schedule 20-minute founder call
3. Send deal one-pager

## If Any Item Fails → Do NOT Share Deck
- Log reason in CRM
- Send polite disqualification email if unaccredited
- Flag for Phil review if unclear case
"""
