"""
prompts/document_review.py — Prompts for pitch deck / tear sheet QA.
"""

PROMPT_VERSION = "1.0"

SEQUOIA_REVIEW_PROMPT = """
Review the attached tear sheet and pitch deck for {company_name}.

Grade them from a Sequoia Capital perspective on a scale of 1-10 for each section:
1. Company Purpose clarity
2. Problem definition
3. Solution differentiation
4. Market size credibility
5. Competitive positioning
6. Team strength
7. Financial projections quality
8. Overall investment thesis

For each section scoring below 8, provide specific revision instructions.
Be brutal and specific — this needs to pass Sequoia's investment committee.

Company profile:
{company_profile}

Return as structured JSON with this shape:
{{
  "grades": {{
    "company_purpose": {{"score": 0, "notes": ""}},
    "problem_definition": {{"score": 0, "notes": ""}},
    "solution_differentiation": {{"score": 0, "notes": ""}},
    "market_size_credibility": {{"score": 0, "notes": ""}},
    "competitive_positioning": {{"score": 0, "notes": ""}},
    "team_strength": {{"score": 0, "notes": ""}},
    "financial_projections": {{"score": 0, "notes": ""}},
    "overall_investment_thesis": {{"score": 0, "notes": ""}}
  }},
  "overall_score": 0,
  "critical_revisions": [],
  "strengths": [],
  "investment_readiness": "not_ready | needs_work | investor_ready"
}}
"""

TEAR_SHEET_OUTLINE_PROMPT = """
Generate a professional 1-2 page investor tear sheet outline for {company_name}.

Company details:
{company_profile}

The tear sheet must cover:
1. Company overview (2-3 sentences)
2. Problem being solved
3. Solution / product description
4. Market opportunity (TAM/SAM/SOM)
5. Business model
6. Traction metrics (placeholders if unknown)
7. Team highlights
8. Raise amount and use of funds
9. Contact information

Format as clean markdown with headers and bullet points. Be investor-grade — specific, data-driven, no fluff.
"""

PITCH_DECK_OUTLINE_PROMPT = """
Generate a detailed 11-slide pitch deck outline for {company_name}.

Company details:
{company_profile}

The 11 slides must be exactly:
1. Company Purpose — One-sentence mission
2. Problem — Specific, quantified pain point
3. Solution — How the product solves it
4. Why Now — Market timing, regulatory, or technology catalyst
5. Market Size + Distribution + GTM — TAM/SAM/SOM + go-to-market approach
6. Competition — Positioning matrix vs. competitors
7. Product — Key features, screenshots or demo flow description
8. Business Model — Revenue streams, pricing, unit economics
9. Team — Key founders and advisors with credentials
10. Financials — Projections, historicals, raise amount, invested; must include FCFF, WACC, Income Statement, Assumptions, Balance Sheet, Market Comparisons, Book Value
11. Contact Page — Founder contact info and CTA

Return as JSON:
{{
  "slides": [
    {{"slide_number": 1, "title": "", "key_points": [], "content_guidance": ""}}
  ]
}}
"""

FINANCIAL_REVIEW_PROMPT = """
Review the financial projections for {company_name}.

Company profile:
{company_profile}

Check for the presence and quality of each required financial component:
- FCFF (Free Cash Flow to Firm)
- Weighted Valuation
- Income Statement (3-5 year projections)
- Key Assumptions document
- Balance Sheet
- WACC (Weighted Average Cost of Capital)
- Market Comparisons / Comps
- Book Value

For each component, indicate: present / missing / incomplete.
For missing/incomplete items, provide specific instructions on what to add.

Return as JSON:
{{
  "components": {{
    "fcff": {{"status": "present|missing|incomplete", "notes": ""}},
    "weighted_valuation": {{"status": "present|missing|incomplete", "notes": ""}},
    "income_statement": {{"status": "present|missing|incomplete", "notes": ""}},
    "assumptions": {{"status": "present|missing|incomplete", "notes": ""}},
    "balance_sheet": {{"status": "present|missing|incomplete", "notes": ""}},
    "wacc": {{"status": "present|missing|incomplete", "notes": ""}},
    "market_comparisons": {{"status": "present|missing|incomplete", "notes": ""}},
    "book_value": {{"status": "present|missing|incomplete", "notes": ""}}
  }},
  "missing_items": [],
  "overall_quality": "insufficient | adequate | strong",
  "action_items": []
}}
"""
