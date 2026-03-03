"""
agents/content_agent.py — Video scripts, podcast outreach, press releases, pitch events.

Handles Steps 4, 5, 10, 13: Video scripts, PR, podcast outreach, pitch events.
"""
from typing import List, Optional

from agents.base_agent import BaseAgent
from core.deal import Deal
from integrations.claude_client import ClaudeClient
from prompts.video_script import VIDEO_SCRIPT_PROMPT, PODCAST_OUTREACH_PROMPT, PRESS_RELEASE_PROMPT


# ─── Hardcoded podcast/event data (real API stubbed) ──────────────────────────
_MOCK_PODCASTS_BY_INDUSTRY = {
    "artificial intelligence": [
        {"name": "Lex Fridman Podcast", "host": "Lex Fridman", "email": "contact@lexfridman.com", "focus": "AI, technology, science"},
        {"name": "The TWIML AI Podcast", "host": "Sam Charrington", "email": "sam@twimlai.com", "focus": "Machine learning, AI"},
        {"name": "Gradient Dissent", "host": "Lukas Biewald", "email": "podcast@wandb.com", "focus": "ML practitioners"},
        {"name": "Practical AI", "host": "Chris Benson", "email": "practicalai@changelog.com", "focus": "Practical AI applications"},
        {"name": "The AI Podcast (NVIDIA)", "host": "NVIDIA Team", "email": "media@nvidia.com", "focus": "AI, deep learning"},
        {"name": "Eye on AI", "host": "Craig Smith", "email": "craig@eyeonai.com", "focus": "AI business applications"},
        {"name": "Data Skeptic", "host": "Kyle Polich", "email": "kyle@dataskeptic.com", "focus": "Data science, ML"},
        {"name": "The Robot Brains Podcast", "host": "Pieter Abbeel", "email": "info@robotbrains.fm", "focus": "Robotics, AI"},
        {"name": "AI Alignment Podcast", "host": "Lucas Perry", "email": "lucas@futureoflife.org", "focus": "AI safety"},
        {"name": "Venture Stories", "host": "Erik Torenberg", "email": "erik@villageglobal.vc", "focus": "Startups, VC, AI"},
    ],
    "default": [
        {"name": "How I Built This", "host": "Guy Raz", "email": "hibt@npr.org", "focus": "Entrepreneurs, startups"},
        {"name": "The Tim Ferriss Show", "host": "Tim Ferriss", "email": "tim@fourhourbody.com", "focus": "Entrepreneurs, high performance"},
        {"name": "Masters of Scale", "host": "Reid Hoffman", "email": "contact@mastersofscale.com", "focus": "Scaling startups"},
        {"name": "Acquired", "host": "Ben Gilbert & David Rosenthal", "email": "hello@acquired.fm", "focus": "Company history, strategy"},
        {"name": "The Pitch", "host": "Josh Muccio", "email": "pitch@gimletmedia.com", "focus": "Startup pitches, investors"},
        {"name": "Invest Like the Best", "host": "Patrick O'Shaughnessy", "email": "patrick@joincolossus.com", "focus": "Investing, business"},
        {"name": "The Twenty Minute VC", "host": "Harry Stebbings", "email": "harry@thetwentyminutevc.com", "focus": "VC, startups"},
        {"name": "Startup School Radio", "host": "Y Combinator", "email": "media@ycombinator.com", "focus": "Early-stage startups"},
        {"name": "Entrepreneurial Thought Leaders", "host": "Stanford eCorner", "email": "ecorner@stanford.edu", "focus": "Entrepreneurs"},
        {"name": "Build", "host": "Ravi Gupta", "email": "ravi@sequoiacap.com", "focus": "Company building, VC"},
    ],
}

_MOCK_PITCH_EVENTS = [
    {"name": "TechCrunch Disrupt", "location": "San Francisco, CA", "date": "2026-10-01", "url": "https://techcrunch.com/events/tc-disrupt-2026/", "type": "pitch_competition"},
    {"name": "Y Combinator Demo Day", "location": "San Francisco, CA", "date": "2026-03-15", "url": "https://www.ycombinator.com/demoday", "type": "demo_day"},
    {"name": "SaaStr Annual", "location": "San Mateo, CA", "date": "2026-09-09", "url": "https://www.saastr.com/annual/", "type": "conference"},
    {"name": "Web Summit", "location": "Lisbon, Portugal", "date": "2026-11-04", "url": "https://websummit.com/", "type": "conference"},
    {"name": "Collision Conference", "location": "Toronto, Canada", "date": "2026-06-23", "url": "https://collisionconf.com/", "type": "conference"},
    {"name": "Startup Grind Global", "location": "Redwood City, CA", "date": "2026-02-18", "url": "https://www.startupgrind.com/conference/", "type": "pitch_event"},
    {"name": "LAUNCH Festival", "location": "San Francisco, CA", "date": "2026-03-05", "url": "https://www.launchfestival.com/", "type": "pitch_competition"},
    {"name": "Venture Atlanta", "location": "Atlanta, GA", "date": "2026-10-15", "url": "https://www.ventureatlanta.org/", "type": "pitch_event"},
]


class ContentAgent(BaseAgent):
    """Agent responsible for content generation: video scripts, PR, podcasts, events."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        super().__init__(claude_client)

    def generate_video_script(self, deal: Deal) -> dict:
        """
        Generate a timed founder video script with section breakdown.

        Total runtime: 170 seconds.

        Args:
            deal: Current Deal object.

        Returns:
            Dict with sections list and full_script string.
        """
        self.logger.info(f"[{deal.deal_id}] Generating founder video script for {deal.company_name}")
        prompt = VIDEO_SCRIPT_PROMPT.format(
            company_name=deal.company_name,
            founder_name=deal.founder_name,
            industry=deal.industry,
            company_profile=deal.company_profile_text(),
        )
        result = self.generate_json(prompt)
        self.logger.info(
            f"[{deal.deal_id}] Video script generated — "
            f"{len(result.get('sections', []))} sections, "
            f"{result.get('total_duration_seconds', 0)}s total"
        )
        return result

    def find_podcasts(self, deal: Deal) -> List[dict]:
        """
        Return top 10 podcasts in the deal's industry.

        # TODO: WIRE REAL API — Replace with live podcast search (ListenNotes, Rephonic, etc.)

        Args:
            deal: Current Deal object.

        Returns:
            List of up to 10 podcast dicts.
        """
        self.logger.info(f"[{deal.deal_id}] Finding podcasts for industry: {deal.industry}")
        key = deal.industry.lower()
        podcasts = _MOCK_PODCASTS_BY_INDUSTRY.get(key, _MOCK_PODCASTS_BY_INDUSTRY["default"])
        self.logger.info(f"[{deal.deal_id}] Found {len(podcasts)} podcasts")
        return podcasts[:10]

    def draft_podcast_outreach(self, deal: Deal, podcast: dict) -> dict:
        """
        Draft an outreach email to a podcast host/producer.

        Args:
            deal: Current Deal object.
            podcast: Podcast dict with name, host, email, focus.

        Returns:
            Dict with 'subject' and 'body'.
        """
        self.logger.info(
            f"[{deal.deal_id}] Drafting podcast outreach for {podcast.get('name')}"
        )
        prompt = PODCAST_OUTREACH_PROMPT.format(
            company_name=deal.company_name,
            podcast_name=podcast.get("name", "Unknown Podcast"),
            founder_name=deal.founder_name,
            host_name=podcast.get("host", "Host"),
            podcast_focus=podcast.get("focus", "technology and business"),
            why_fit=f"The company operates in {deal.industry} — directly aligned with the podcast's focus on {podcast.get('focus', 'technology')}.",
            company_profile=deal.company_profile_text(),
        )
        result = self.generate_json(prompt)
        return result

    def draft_press_release(self, deal: Deal) -> dict:
        """
        Generate a press release announcing the fundraising round.

        Args:
            deal: Current Deal object.

        Returns:
            Dict with headline, body paragraphs, and full_text.
        """
        self.logger.info(f"[{deal.deal_id}] Drafting press release for {deal.company_name}")
        prompt = PRESS_RELEASE_PROMPT.format(
            company_name=deal.company_name,
            company_profile=deal.company_profile_text(),
            raise_amount=deal.raise_amount,
            founder_name=deal.founder_name,
        )
        result = self.generate_json(prompt)
        return result

    def find_pitch_events(self, deal: Deal) -> List[dict]:
        """
        Return upcoming pitch events and investor meetups relevant to the deal.

        # TODO: WIRE REAL API — Eventbrite, F6S, or AngelList event feeds

        Args:
            deal: Current Deal object.

        Returns:
            List of pitch event dicts.
        """
        self.logger.info(f"[{deal.deal_id}] Finding pitch events for {deal.company_name}")
        # Return all mock events — in real API, would filter by industry/location
        self.logger.info(f"[{deal.deal_id}] Found {len(_MOCK_PITCH_EVENTS)} pitch events")
        return _MOCK_PITCH_EVENTS
