"""
prompts/weekly_report.py — Prompts for weekly progress report generation.
"""

PROMPT_VERSION = "1.0"

WEEKLY_REPORT_PROMPT = """
Generate a weekly capital formation progress report for {company_name}.

Report Week: {week_number}
Reporting Period: {start_date} to {end_date}

Current deal statistics:
- Investors contacted this week: {investors_contacted_this_week}
- Total investors contacted: {total_investors_contacted}
- Investors responded: {total_responded}
- Response rate: {response_rate:.1%}
- Meetings scheduled: {meetings_scheduled}
- Meetings completed: {meetings_completed}
- Meeting conversion rate: {meeting_conversion:.1%}
- Commitments received: {commitments_received}
- Total committed: ${total_committed:,.0f}
- Target raise: ${raise_amount:,.0f}
- Pipeline value (interested but not committed): ${pipeline_value:,.0f}

Campaign status:
- MeetAlfred campaign active: {campaign_active}
- Current outreach week: {outreach_week}
- Steps completed: {completed_steps}

Generate a professional weekly report covering:
1. Executive Summary (3-4 sentences)
2. Investor Outreach Metrics table
3. Key Highlights & Wins this week
4. Issues & Blockers
5. Next Week Action Plan (with specific targets)
6. Alerts (if response rate < 20% or meeting conversion < 5%)

Format as clean markdown. Be direct and data-driven.

Return the full report as a markdown string.
"""

COMPLIANCE_LOG_PROMPT = """
Generate a legal document and compliance tracking log for {company_name}.

Current document status:
{document_status}

NDA signed by: {nda_signed_by}
Investors contacted: {investors_contacted_count}

Generate a structured compliance log covering:
1. Document status table (all required docs with status)
2. NDA tracking (signed vs pending)
3. Wire/ACH verification checklist
4. Outstanding legal action items
5. Flag items for Dock Walls review

Return as markdown.
"""
