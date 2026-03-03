"""
prompts/investor_search.py — Prompts for investor discovery and scoring.
"""

PROMPT_VERSION = "1.0"

INVESTOR_SEARCH_PROMPT = """
Search for public investor data and online investor intent signals ranked 20 out of 20
for active investors seeking to invest in {company_website}.

Review the attached company profile. Provide public contact info for:
- Full name
- Email
- Phone
- LinkedIn URL
- X (Twitter) handle
- Website

Company Profile:
{company_profile}

Return as a JSON array of 20 investor objects, ranked by investment fit score (0-100):
[
  {{
    "rank": 1,
    "full_name": "",
    "firm": "",
    "title": "",
    "email": "",
    "phone": "",
    "linkedin_url": "",
    "twitter_handle": "",
    "website": "",
    "fit_score": 0,
    "investment_thesis": "",
    "why_good_fit": "",
    "portfolio_companies": [],
    "check_size_range": ""
  }}
]

Rules:
- Use specific named contacts only — never generic contact@firm.com
- Include only investors actively deploying capital at seed/Series A stage
- Rank by relevance to industry: {industry}
- Fit score is 0-100 based on industry match, check size, and recent activity
"""

INVESTOR_FIT_SCORE_PROMPT = """
Score the investment fit between the following investor and company on a scale of 0.0 to 1.0.

Company:
{company_profile}

Investor:
Name: {investor_name}
Firm: {investor_firm}
Investment thesis: {investor_thesis}
Portfolio: {investor_portfolio}
Check size: {investor_check_size}

Return as JSON:
{{
  "fit_score": 0.0,
  "reasoning": "",
  "alignment_factors": [],
  "misalignment_factors": []
}}
"""
