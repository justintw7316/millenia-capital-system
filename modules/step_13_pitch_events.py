"""
modules/step_13_pitch_events.py — Step 13: Pitch Events

Find upcoming pitch events, generate event calendar, pitch prep checklist.
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
    Step 13: Find pitch events and generate prep materials.
    All event attendance is human-executed.
    """
    logger.info(f"[{deal.deal_id}] ▶ Step 13: Pitch Events")

    errors = []
    human_actions = []
    outputs = {}

    output_dir = OUTPUT_DIR / deal.deal_id
    output_dir.mkdir(parents=True, exist_ok=True)

    agent = ContentAgent()

    # ── Find pitch events ──────────────────────────────────────────────────────
    try:
        events = agent.find_pitch_events(deal)
        events_path = output_dir / "pitch_events.json"
        with open(events_path, "w") as f:
            json.dump({
                "deal_id": deal.deal_id,
                "company": deal.company_name,
                "generated_at": datetime.utcnow().isoformat(),
                "events": events,
            }, f, indent=2)
        outputs["pitch_events_json"] = str(events_path)
        logger.info(f"[{deal.deal_id}] Found {len(events)} pitch events")
    except Exception as e:
        errors.append(f"Pitch event search failed: {e}")
        logger.error(f"[{deal.deal_id}] Pitch event error: {e}")
        events = []

    # ── Generate event calendar markdown ─────────────────────────────────────
    calendar_md = _generate_event_calendar(deal, events)
    calendar_path = output_dir / "pitch_events_calendar.md"
    calendar_path.write_text(calendar_md)
    outputs["pitch_events_calendar"] = str(calendar_path)

    # ── Generate pitch prep checklist ─────────────────────────────────────────
    prep_checklist = _generate_pitch_prep_checklist(deal)
    prep_path = output_dir / "pitch_prep_checklist.md"
    prep_path.write_text(prep_checklist)
    outputs["pitch_prep_checklist"] = str(prep_path)

    human_actions.extend([
        "Register for relevant pitch events listed in pitch_events_calendar.md.",
        "Complete pitch_prep_checklist.md at least 2 weeks before each event.",
        "Practice pitch with Millenia Ventures team before attending events.",
        "All attendance and travel is human-executed.",
    ])

    deal.log_step("13", "completed", f"Pitch events calendar generated: {len(events)} events found.", outputs)

    return deal, {
        "success": len(errors) == 0,
        "output": outputs,
        "errors": errors,
        "human_actions_required": human_actions,
    }


def _generate_event_calendar(deal: Deal, events: list) -> str:
    lines = [
        f"# Pitch Events Calendar — {deal.company_name}",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d')}",
        f"**Industry:** {deal.industry.title()}",
        "",
        "---",
        "",
        "## Upcoming Events",
        "",
        "| Event | Date | Location | Type | Registration | Priority |",
        "|-------|------|----------|------|-------------|----------|",
    ]

    for event in events:
        name = event.get("name", "Unknown")
        date = event.get("date", "TBD")
        location = event.get("location", "TBD")
        event_type = event.get("type", "event").replace("_", " ").title()
        url = event.get("url", "#")
        # Simple priority: pitch competitions and demo days are highest
        priority = "🔴 High" if event.get("type") in ["pitch_competition", "demo_day"] else "🟡 Medium"
        lines.append(f"| {name} | {date} | {location} | {event_type} | [Register]({url}) | {priority} |")

    lines.extend([
        "",
        "---",
        "",
        "## Registration Tracking",
        "",
        "| Event | Registered | Materials Submitted | Travel Booked | Notes |",
        "|-------|-----------|--------------------|--------------| ------|",
    ])
    for event in events:
        lines.append(f"| {event.get('name', 'Unknown')} | [ ] | [ ] | [ ] | |")

    lines.extend([
        "",
        "## Notes",
        f"- Priority: pitch competitions and demo days where {deal.company_name} can present live",
        "- Budget for travel: confirm with Phil before registering for out-of-state events",
        "- Apply 6-8 weeks before event deadline",
        "- Prepare tailored pitch for each event's audience",
    ])

    return "\n".join(lines)


def _generate_pitch_prep_checklist(deal: Deal) -> str:
    return f"""# Pitch Preparation Checklist — {deal.company_name}

**Complete at least 2 weeks before each pitch event.**

---

## 6 Weeks Before Event
- [ ] Register for the event (get confirmation email)
- [ ] Research the event's investor audience
- [ ] Review last year's winning pitches (if available)
- [ ] Confirm pitch format: length, slide count, Q&A time

## 4 Weeks Before Event
- [ ] Update pitch deck to latest version
- [ ] Tailor slides for this specific audience
- [ ] Prepare demo (if applicable) — test all tech
- [ ] Research key investors attending — identify top 5 targets
- [ ] Prepare one-pager / leave-behind

## 2 Weeks Before Event
- [ ] Do 3 full practice runs with Millenia Ventures team
- [ ] Record practice run and review footage
- [ ] Refine answers for common tough questions:
  - "What's your biggest risk?"
  - "Why are you the right team?"
  - "What if [large company] does this?"
  - "What's your exit strategy?"
  - "What's your burn rate?"
- [ ] Confirm all technology works (clicker, laptop, adapters)
- [ ] Prepare business cards

## 1 Week Before Event
- [ ] Confirm registration and event logistics
- [ ] Book travel and accommodation (if needed)
- [ ] Do final practice run
- [ ] Download pitch deck to device (don't rely on internet)
- [ ] Set up investor meeting requests via LinkedIn

## Day of Event
- [ ] Arrive 30 minutes early
- [ ] Test tech setup in the room
- [ ] Review top 5 target investor profiles
- [ ] Collect contact info from all conversations
- [ ] Take notes on every investor conversation

## Post-Event (Within 24 hours)
- [ ] Send follow-up emails to all interested investors
- [ ] Add new contacts to investor_list.json
- [ ] Report results to Millenia Ventures
- [ ] Schedule follow-up calls with interested investors

## Materials to Bring
- [ ] Pitch deck (on laptop + USB backup)
- [ ] One-pagers (printed, 25 copies)
- [ ] Business cards (50+ copies)
- [ ] QR code linking to {deal.company_website}
- [ ] NDA forms (digital or printed)
"""
