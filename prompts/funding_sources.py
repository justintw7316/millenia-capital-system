"""
prompts/funding_sources.py — Prompts for alternative funding source research.
"""

PROMPT_VERSION = "1.0"

ALT_FUNDING_PROMPT = """
Provide grant, sponsored capital, private lending and alternative funding sources
for {company_name} in the U.S. at seed stage.

Company details:
{company_profile}

Include for each source:
- Organization name
- Contact name
- Email
- Phone
- Website
- Why it's a fit for this company
- Funding type (grant / loan / equity / revenue-based / other)
- Typical amount range
- Application deadline (if known)

Only show 10 out of 10 matches. Rank by best fit.
Return as JSON array:
[
  {{
    "rank": 1,
    "organization_name": "",
    "contact_name": "",
    "email": "",
    "phone": "",
    "website": "",
    "funding_type": "",
    "typical_amount_range": "",
    "application_deadline": "",
    "why_good_fit": ""
  }}
]
"""

ALT_FUNDING_EMAIL_PROMPT = """
Draft a custom email for {source_name} introducing {company_name}.

Use bullet points to:
1. Introduce the company and its mission
2. Explain why {company_name} is a strong strategic fit for {source_name} to fund

Contact name: {contact_name}
Include first name in salutation.
Keep it under 300 words. Professional and specific.
Funding type context: {funding_type}

Return as JSON:
{{
  "subject": "",
  "body": ""
}}
"""

MEETALFRED_ALT_FUNDING_PROMPT = """
Generate a LinkedIn outreach message for alternative funding source {source_name}.

Company seeking funding: {company_name}
Funding type: {funding_type}
Why this source is a fit: {why_fit}

Create a professional LinkedIn connection request message (under 300 characters).

Return as JSON:
{{
  "connection_request": "",
  "follow_up_message": ""
}}
"""
