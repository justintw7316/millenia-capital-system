"""
modules/step_07c_meetalfred_campaign.py — Step 7c: MeetAlfred Campaign

Creates LinkedIn Sales Navigator criteria and MeetAlfred campaign draft.
"""
import json
from datetime import datetime
from typing import Tuple

from core.deal import Deal
from core.logger import get_logger
from agents.campaign_agent import CampaignAgent
from integrations.meetalfred_client import MeetAlfredClient
from config import OUTPUT_DIR

logger = get_logger(__name__)


def run(deal: Deal, config: dict) -> Tuple[Deal, dict]:
    """
    Step 7c: Generate Sales Navigator criteria and MeetAlfred campaign draft.

    Requires Phil approval before launch. Das executes after approval.
    """
    logger.info(f"[{deal.deal_id}] ▶ Step 7c: MeetAlfred Campaign")

    errors = []
    human_actions = []
    outputs = {}

    output_dir = OUTPUT_DIR / deal.deal_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Load investor list ─────────────────────────────────────────────────────
    investor_list_path = output_dir / "investor_list.json"
    investors = []
    if investor_list_path.exists():
        with open(investor_list_path) as f:
            investors = json.load(f).get("investors", [])

    campaign_agent = CampaignAgent()
    meetalfred = MeetAlfredClient()

    # ── Generate Sales Navigator search criteria ──────────────────────────────
    sales_nav_criteria = _build_sales_nav_criteria(deal)
    criteria_path = output_dir / "sales_navigator_criteria.json"
    with open(criteria_path, "w") as f:
        json.dump(sales_nav_criteria, f, indent=2)
    outputs["sales_navigator_criteria"] = str(criteria_path)

    # ── Match segments for A/B campaign variant targeting ────────────────────
    segment_summary = {}
    for inv in investors:
        seg = inv.get("match_segment", "unsegmented")
        segment_summary.setdefault(seg, {"count": 0, "investors": []})
        segment_summary[seg]["count"] += 1
        segment_summary[seg]["investors"].append(inv.get("full_name", "Unknown"))
    if segment_summary:
        segments_path = output_dir / "match_segments_07c.json"
        with open(segments_path, "w") as f:
            json.dump({
                "deal_id": deal.deal_id,
                "generated_at": datetime.utcnow().isoformat(),
                "segments": segment_summary,
                "ab_variant_recommendation": {
                    "variant_a": "Highest-thesis-alignment segment (e.g., ai_infra)",
                    "variant_b": "Warm-network or secondary segment for contrast",
                },
            }, f, indent=2)
        outputs["match_segments"] = str(segments_path)

    # ── Create campaign structure ─────────────────────────────────────────────
    try:
        campaign_data = campaign_agent.create_meetalfred_campaign(deal, investors)

        # Try to register with MeetAlfred (stubbed)
        try:
            campaign_id = meetalfred.create_campaign(campaign_data)
            campaign_data["campaign_id"] = campaign_id
            deal.meetalfred_campaign_id = campaign_id
            logger.info(f"[{deal.deal_id}] MeetAlfred campaign created: {campaign_id}")
        except Exception as e:
            errors.append(f"MeetAlfred campaign creation failed: {e} — draft saved locally.")
            logger.warning(f"[{deal.deal_id}] MeetAlfred API error (saving draft): {e}")
            human_actions.append(
                "MeetAlfred campaign creation failed — manually upload meetalfred_campaign_draft.json."
            )

        # Save campaign draft
        campaign_path = output_dir / "meetalfred_campaign_draft.json"
        with open(campaign_path, "w") as f:
            json.dump(campaign_data, f, indent=2)
        outputs["meetalfred_campaign"] = str(campaign_path)

        # ── A/B test variants ──────────────────────────────────────────────────
        sequence = campaign_data.get("sequence", [])
        connection_msg = ""
        for step in sequence:
            if step.get("type") == "connection_request":
                connection_msg = step.get("body", "")
                break

        ab_md = _generate_ab_variants_doc(deal, campaign_data.get("ab_variants", {}), connection_msg)
        ab_path = output_dir / "ab_test_variants.md"
        ab_path.write_text(ab_md)
        outputs["ab_test_variants"] = str(ab_path)

        logger.info(f"[{deal.deal_id}] Campaign draft and A/B variants saved")

    except Exception as e:
        errors.append(f"Campaign generation failed: {e}")
        logger.error(f"[{deal.deal_id}] Campaign error: {e}")

    human_actions.extend([
        "⚠️ PHIL APPROVAL REQUIRED before campaign launch. Review meetalfred_campaign_draft.json.",
        "After Phil approves: Das to launch the campaign in MeetAlfred.",
        "Review sales_navigator_criteria.json and adjust Search Navigator filters as needed.",
        "A/B test: Select variant A or B for connection request before launch.",
        "Use match_segments_07c.json to split A/B variants by segment (e.g., thesis-aligned vs warm-network).",
    ])

    deal.log_step("07c", "completed", "MeetAlfred campaign draft created — awaiting Phil approval.", outputs)

    return deal, {
        "success": len(errors) == 0,
        "output": outputs,
        "errors": errors,
        "human_actions_required": human_actions,
    }


def _build_sales_nav_criteria(deal: Deal) -> dict:
    """Build LinkedIn Sales Navigator search criteria for the deal's target investors."""
    # Industry-to-VC-focus mapping
    industry_keywords = {
        "artificial intelligence": ["AI", "Machine Learning", "Deep Tech", "SaaS"],
        "fintech": ["Fintech", "Financial Technology", "Banking", "Payments"],
        "healthtech": ["Health Tech", "Digital Health", "MedTech", "Healthcare"],
        "cleantech": ["CleanTech", "Climate Tech", "Sustainability", "Green Energy"],
        "edtech": ["EdTech", "Education Technology", "E-Learning"],
    }
    focus_keywords = industry_keywords.get(deal.industry.lower(), [deal.industry.title()])

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "deal_id": deal.deal_id,
        "company": deal.company_name,
        "industry": deal.industry,
        "title_filters": [
            "General Partner",
            "Managing Partner",
            "Partner",
            "Principal",
            "Venture Partner",
            "Investment Director",
            "Head of Investments",
            "Angel Investor",
        ],
        "industry_keywords": focus_keywords,
        "geography": ["United States", "Canada"],
        "company_type": ["Venture Capital", "Private Equity", "Family Office", "Angel Network"],
        "seniority": ["Director", "VP", "C-Level", "Partner", "Owner"],
        "exclusions": ["Recruiter", "Advisor", "Student", "Intern"],
        "raise_amount_context": deal.raise_amount,
        "notes": (
            "Filter for investors actively posting about seed/early-stage deals. "
            "Priority: investors who have posted about portfolio investments in last 90 days."
        ),
    }


def _generate_ab_variants_doc(deal: Deal, ab_variants: dict, original: str) -> str:
    return f"""# A/B Test Variants — MeetAlfred Connection Request
**Company:** {deal.company_name}
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d')}

## Original Message
{original or 'Not available'}

---

## Variant A
{ab_variants.get('variant_a', 'Not generated')}

**Character count:** {len(ab_variants.get('variant_a', ''))} / 300

---

## Variant B
{ab_variants.get('variant_b', 'Not generated')}

**Character count:** {len(ab_variants.get('variant_b', ''))} / 300

---

## Testing Instructions
1. Split the investor list 50/50 between Variant A and Variant B
2. Run both for 2 weeks
3. Compare connection acceptance rates
4. Continue with the higher-performing variant for remaining outreach

## Success Metrics
- Connection acceptance rate (target: > 25%)
- Reply rate after connection (target: > 10%)
- Meeting conversion rate (target: > 5%)
"""
