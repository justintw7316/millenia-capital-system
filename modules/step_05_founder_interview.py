"""
modules/step_05_founder_interview.py — Step 5: Founder Interview

Streamyard scheduling email, 20 investor interview questions, clip distribution checklist.
"""
from datetime import datetime
from typing import Tuple

from core.deal import Deal
from core.logger import get_logger
from config import OUTPUT_DIR

logger = get_logger(__name__)

# ── 20 Hardcoded investor interview questions ─────────────────────────────────
INVESTOR_QUESTIONS = [
    "Tell us about yourself and your background — what led you to start this company?",
    "What specific problem are you solving, and why does it matter now?",
    "How did you validate that this problem is real and significant before building the product?",
    "Walk us through your solution — what does your product do and how does it work?",
    "Who is your primary customer, and what does their decision-making process look like?",
    "What is your current traction — revenue, users, growth rate, key partnerships?",
    "How big is the total addressable market, and how did you arrive at that number?",
    "Who are your main competitors, and what makes you different or better?",
    "What is your go-to-market strategy — how do you plan to acquire customers at scale?",
    "Walk us through your business model — how do you make money?",
    "What are your key unit economics — CAC, LTV, payback period, gross margin?",
    "Tell us about your team — who are the key members and why are they the right people for this?",
    "What are the most significant risks to your business, and how are you mitigating them?",
    "How much are you raising, at what valuation, and how will you use the capital?",
    "What milestones will this raise allow you to hit, and over what timeframe?",
    "Have you raised money before? If so, from whom and how much?",
    "What does your 3-year financial trajectory look like — revenue, margin, headcount?",
    "What would make this a 10x or 100x return for investors?",
    "Who else is on your cap table, and what are the key terms investors should know?",
    "What is your exit strategy — IPO, strategic acquisition, or other path to liquidity?",
]


def run(deal: Deal, config: dict) -> Tuple[Deal, dict]:
    """
    Step 5: Generate founder interview scheduling email, 20 questions, and clip distribution checklist.
    """
    logger.info(f"[{deal.deal_id}] ▶ Step 5: Founder Interview")

    errors = []
    human_actions = []
    outputs = {}

    output_dir = OUTPUT_DIR / deal.deal_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Check if founder declined / step skipped ──────────────────────────────
    if "05" in deal.skipped_steps:
        logger.info(f"[{deal.deal_id}] Step 5 marked as skipped")
        deal.log_step("05", "skipped", "Founder interview skipped.")
        return deal, {
            "success": True,
            "output": {"skipped": True},
            "errors": [],
            "human_actions_required": [],
        }

    # ── Generate scheduling email ─────────────────────────────────────────────
    scheduling_email = _generate_scheduling_email(deal)
    email_path = output_dir / "interview_scheduling_email.md"
    email_path.write_text(scheduling_email)
    outputs["scheduling_email"] = str(email_path)

    # ── Generate questions document ───────────────────────────────────────────
    questions_doc = _generate_questions_doc(deal)
    questions_path = output_dir / "investor_questions.md"
    questions_path.write_text(questions_doc)
    outputs["investor_questions"] = str(questions_path)

    # ── Generate clip distribution checklist ──────────────────────────────────
    clip_checklist = _generate_clip_checklist(deal)
    clip_path = output_dir / "clip_distribution_checklist.md"
    clip_path.write_text(clip_checklist)
    outputs["clip_distribution_checklist"] = str(clip_path)

    # ── Generate founder follow-up sequence if unresponsive ──────────────────
    followup_sequence = _generate_founder_followup(deal)
    followup_path = output_dir / "founder_interview_followup_sequence.md"
    followup_path.write_text(followup_sequence)
    outputs["founder_followup_sequence"] = str(followup_path)

    human_actions.extend([
        f"Send interview_scheduling_email.md to {deal.founder_name} at {deal.founder_email}.",
        "Schedule Streamyard recording session and send calendar invite.",
        "Record the 20-question investor interview.",
        "Edit interview into 5-10 clips using Opus.Pro.",
        "Distribute clips per clip_distribution_checklist.md.",
    ])

    deal.log_step("05", "completed", "Interview scheduling email, 20 questions, and clip checklist generated.", outputs)

    return deal, {
        "success": len(errors) == 0,
        "output": outputs,
        "errors": errors,
        "human_actions_required": human_actions,
    }


def _generate_scheduling_email(deal: Deal) -> str:
    return f"""# Interview Scheduling Email — {deal.company_name}

**To:** {deal.founder_email}
**Subject:** Investor Interview Session — Scheduling Your Streamyard Recording

---

Hi {deal.founder_name.split()[0]},

I hope you're doing well. We're ready to schedule your investor interview recording on Streamyard — this is an important asset that will be shared with prospective investors throughout the capital formation process.

**What this is:**
A structured 20-question interview where you'll speak directly to investors. This will be recorded, edited into clips, and distributed across our investor outreach channels.

**Format:**
- Platform: Streamyard (link will be sent)
- Duration: Approximately 60-90 minutes (we'll take multiple takes)
- Location: Wherever you have a professional background and strong internet

**The 20 questions are attached** in a separate document so you can prepare. You do not need to memorize them — speak naturally and from experience.

**To schedule:**
Please reply with 3 available time slots over the next 2 weeks. We'll confirm and send a calendar invite with the Streamyard link.

**Technical requirements:**
- Wired internet connection (preferred) or strong WiFi
- External microphone or headset
- Good front-facing lighting
- Clean, professional background

Let me know if you have any questions before we get started.

Best,
Millenia Ventures Team

---
*If you are unavailable or wish to reschedule, please reply within 48 hours. See the attached follow-up sequence for timing.*
"""


def _generate_questions_doc(deal: Deal) -> str:
    lines = [
        f"# Investor Interview Questions — {deal.company_name}",
        f"**Founder:** {deal.founder_name}",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d')}",
        "",
        "Prepare thoughtful, specific answers for each question. Use real data and examples wherever possible.",
        "",
        "---",
        "",
    ]
    for i, q in enumerate(INVESTOR_QUESTIONS, 1):
        lines.append(f"**Q{i}.** {q}")
        lines.append("")
        lines.append("*Your answer:*")
        lines.append("")
        lines.append("_____________________________________________")
        lines.append("")

    return "\n".join(lines)


def _generate_clip_checklist(deal: Deal) -> str:
    return f"""# Clip Distribution Checklist — {deal.company_name} Investor Interview

**Post-Recording Steps:**

## Editing
- [ ] Upload raw interview to Opus.Pro
- [ ] Generate 7-10 short clips (30-90 seconds each)
- [ ] Add captions to all clips
- [ ] Create 1 highlight reel (3-4 minutes)
- [ ] Export all clips as MP4 (1080p)

## Distribution
| Clip | Platform | Posted | Notes |
|------|----------|--------|-------|
| Clip 1: Problem/Solution | LinkedIn + X | [ ] | |
| Clip 2: Market Opportunity | LinkedIn | [ ] | |
| Clip 3: Team Background | LinkedIn + X | [ ] | |
| Clip 4: Traction Metrics | LinkedIn | [ ] | |
| Clip 5: Ask + ROI | X | [ ] | |
| Highlight Reel | YouTube + LinkedIn | [ ] | |
| Full Interview | YouTube (unlisted) | [ ] | Share link with interested investors |

## Investor Outreach Integration
- [ ] Add best clip link to investor outreach emails
- [ ] Embed highlight reel in tear sheet email signature
- [ ] Share in relevant LinkedIn investor groups
- [ ] Send highlight reel to all investors in active outreach

## Tracking
- [ ] Log all post performance weekly
- [ ] Report clip view counts to Millenia Ventures
"""


def _generate_founder_followup(deal: Deal) -> str:
    return f"""# Founder Interview Follow-Up Sequence

**Use if founder is unresponsive to scheduling email.**

**Trigger:** No response within 48 hours of initial scheduling email.

---

## Follow-Up 1 (48 hours after initial email)

**Subject:** Quick follow-up — Interview Scheduling

Hi {deal.founder_name.split()[0]},

Just following up on my email about scheduling your investor interview on Streamyard.

This recording is a key part of getting your raise in front of investors — it typically generates 3-5x more engagement than a cold email.

Can you share 2-3 available time slots this week?

Best,
Millenia Ventures Team

---

## Follow-Up 2 (96 hours / 4 days after initial email)

**Subject:** Last attempt — Interview Scheduling for {deal.company_name}

Hi {deal.founder_name.split()[0]},

I want to make sure this doesn't fall through the cracks. The investor interview is one of the most effective tools in your capital formation process.

If scheduling has been difficult, I can work around your availability — including evenings or weekends.

Alternatively, if you'd prefer to skip this step for now, please let me know and we'll proceed with the written materials only.

Best,
Millenia Ventures Team

---

## Follow-Up 3 (7 days after initial email)

**Subject:** Final reminder — Investor Interview

Hi {deal.founder_name.split()[0]},

This is our final scheduling attempt for the investor interview. If we don't hear back, we'll proceed with the pipeline using written materials only and revisit the video later.

If you'd like to proceed, please reply with your availability.

Thank you,
Millenia Ventures Team

---

*If no response after 3 attempts: log as unresponsive, mark step 05 as deferred, continue pipeline.*
"""
