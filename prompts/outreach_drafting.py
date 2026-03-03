"""
prompts/outreach_drafting.py — Prompts for multi-platform outreach message drafting.
"""

PROMPT_VERSION = "1.0"

OUTREACH_DRAFT_PROMPT = """
Draft a custom message for investor {investor_name} at {investor_firm}.

About the company:
{company_bullets}

Strategic fit bullets (why this investor is a great match):
{fit_bullets}

Create 6 separate messages — one per platform. Each must be distinct in tone and format:
1. Web Contact Form (concise, 150 words max)
2. LinkedIn Message (with subject line, professional, 200 words max)
3. Email (full format with subject line, 300 words max)
4. SMS (under 160 characters)
5. WhatsApp (conversational, 200 words max)
6. X/Twitter DM (under 280 characters)

Rules:
- Direct, professional, fluff-free
- Include bullet points for company highlights
- Include bullet points for why this investor is a strategic fit
- Never use generic greetings
- Address investor by first name

Return as JSON:
{{
  "investor_name": "{investor_name}",
  "investor_firm": "{investor_firm}",
  "messages": {{
    "web_contact_form": {{
      "body": ""
    }},
    "linkedin": {{
      "subject": "",
      "body": ""
    }},
    "email": {{
      "subject": "",
      "body": ""
    }},
    "sms": {{
      "body": ""
    }},
    "whatsapp": {{
      "body": ""
    }},
    "twitter_dm": {{
      "body": ""
    }}
  }}
}}
"""

FOLLOWUP_PROMPT = """
Draft week {week_number} follow-up message for investor {investor_name}.

Company: {company_name}
New progress this week: {progress_update}
Platform: {platform}

Keep it brief, reference prior contact, and include one new compelling data point.
Previous messages sent: {message_history}

Rules:
- 2-3 sentences maximum for SMS/Twitter
- 150 words max for LinkedIn/WhatsApp
- 250 words max for email
- Reference week number naturally
- Include one specific new milestone or metric

Return as JSON:
{{
  "week": {week_number},
  "platform": "{platform}",
  "investor_name": "{investor_name}",
  "subject": "",
  "body": ""
}}
"""

MEETALFRED_SEQUENCE_PROMPT = """
Generate a LinkedIn outreach message sequence for a MeetAlfred campaign targeting investors.

Company: {company_name}
Target investor profile: {investor_profile}
Industry: {industry}

Create 3 messages in sequence:
1. Connection request (under 300 characters — LinkedIn limit)
2. Follow-up message 1 (sent 3 days after connection, 200 words max)
3. Follow-up message 2 (sent 7 days after message 1, 150 words max)

Also generate 2 A/B variants of the connection request.

Return as JSON:
{{
  "sequence": [
    {{"step": 1, "type": "connection_request", "body": "", "delay_days": 0}},
    {{"step": 2, "type": "follow_up_1", "body": "", "delay_days": 3}},
    {{"step": 3, "type": "follow_up_2", "body": "", "delay_days": 7}}
  ],
  "ab_variants": {{
    "variant_a": "",
    "variant_b": ""
  }}
}}
"""
