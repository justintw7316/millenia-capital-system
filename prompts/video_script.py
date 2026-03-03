"""
prompts/video_script.py — Prompts for founder video script generation.
"""

PROMPT_VERSION = "1.0"

VIDEO_SCRIPT_PROMPT = """
Write a punchy, investor-grade founder video script for {company_name}.

Founder: {founder_name}
Industry: {industry}
Company profile:
{company_profile}

The script must follow this exact timed breakdown (170 seconds total):
- Intro: 10 seconds — Who is the founder and what does the company do
- Product: 15 seconds — What the product is in plain English
- Problem & Solution: 30 seconds — Specific problem and how the product solves it
- Traction: 30 seconds — Key metrics, customers, revenue, growth
- Market + Edge: 20 seconds — Market size and competitive advantage
- Team: 20 seconds — Key team credentials
- Ask + ROI: 30 seconds — Amount raising, valuation, investor ROI potential
- CTA: 15 seconds — What you want the investor to do next

Rules:
- Write as spoken word — conversational but professional
- No buzzwords or jargon
- Every sentence must add value
- Founder speaks directly to camera

Return as JSON:
{{
  "sections": [
    {{
      "section": "Intro",
      "duration_seconds": 10,
      "script": "",
      "notes": ""
    }},
    {{
      "section": "Product",
      "duration_seconds": 15,
      "script": "",
      "notes": ""
    }},
    {{
      "section": "Problem & Solution",
      "duration_seconds": 30,
      "script": "",
      "notes": ""
    }},
    {{
      "section": "Traction",
      "duration_seconds": 30,
      "script": "",
      "notes": ""
    }},
    {{
      "section": "Market + Edge",
      "duration_seconds": 20,
      "script": "",
      "notes": ""
    }},
    {{
      "section": "Team",
      "duration_seconds": 20,
      "script": "",
      "notes": ""
    }},
    {{
      "section": "Ask + ROI",
      "duration_seconds": 30,
      "script": "",
      "notes": ""
    }},
    {{
      "section": "CTA",
      "duration_seconds": 15,
      "script": "",
      "notes": ""
    }}
  ],
  "total_duration_seconds": 170,
  "full_script": ""
}}
"""

PODCAST_OUTREACH_PROMPT = """
Write a podcast outreach email for {company_name} to appear on {podcast_name}.

Founder: {founder_name}
Podcast host/producer: {host_name}
Podcast focus: {podcast_focus}
Why a good fit: {why_fit}
Company profile:
{company_profile}

Rules:
- Subject line: specific and compelling
- Body: under 200 words
- Include 3 specific episode topic ideas
- Reference the podcast specifically
- Pitch the founder's credentials, not just the company

Return as JSON:
{{
  "subject": "",
  "body": ""
}}
"""

PRESS_RELEASE_PROMPT = """
Write a professional press release for {company_name} announcing their fundraising round.

Company profile:
{company_profile}

Raise amount: ${raise_amount:,.0f}
Founder: {founder_name}

Format:
- Dateline: [CITY, DATE]
- Headline: Compelling, factual
- Subheadline: One supporting sentence
- Body: 3-4 paragraphs covering the raise, product, market, and team
- Boilerplate: Standard company description
- Contact: Press contact info

Return as JSON:
{{
  "headline": "",
  "subheadline": "",
  "dateline": "",
  "body_paragraphs": [],
  "boilerplate": "",
  "press_contact": {{
    "name": "",
    "email": "",
    "phone": ""
  }},
  "full_text": ""
}}
"""
