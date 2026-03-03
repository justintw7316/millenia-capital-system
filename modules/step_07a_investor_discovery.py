"""
modules/step_07a_investor_discovery.py — Step 7a: Investor Discovery

Finds 20 ranked investors, enriches contacts via Apollo, validates data.
Critical gate: requires tear sheet to be at least DRAFT before running.
"""
import json
import csv
from datetime import datetime
from typing import Tuple

from core.deal import Deal, DocumentStatus
from core.logger import get_logger
from integrations.apollo_client import ApolloClient
from config import OUTPUT_DIR
from matching import HybridMatchingService

logger = get_logger(__name__)


def run(deal: Deal, config: dict) -> Tuple[Deal, dict]:
    """
    Step 7a: Investor discovery and contact enrichment.

    Critical gate: tear sheet must be at least DRAFT status.
    """
    logger.info(f"[{deal.deal_id}] ▶ Step 7a: Investor Discovery")

    errors = []
    human_actions = []
    outputs = {}

    output_dir = OUTPUT_DIR / deal.deal_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Critical gate: tear sheet must exist ─────────────────────────────────
    if deal.documents.tear_sheet == DocumentStatus.MISSING:
        msg = (
            "CRITICAL GATE: Tear sheet is missing. Step 7a (Investor Discovery) cannot proceed "
            "without at least a draft tear sheet. Run Step 2 first."
        )
        logger.error(f"[{deal.deal_id}] {msg}")
        deal.log_step("07a", "blocked", msg)
        return deal, {
            "success": False,
            "output": {},
            "errors": [msg],
            "human_actions_required": [
                "Complete Step 2 to generate a tear sheet draft before running investor discovery."
            ],
        }

    apollo = ApolloClient()
    matcher = HybridMatchingService()

    # ── Hybrid retrieval + reranking (filters + vector + keyword) ────────────
    try:
        match_run = matcher.run_match(deal, top_k=20, candidate_target=300)
        investors = matcher.results_to_outreach_records(match_run)
        logger.info(
            f"[{deal.deal_id}] Hybrid matcher ranked {len(investors)} investors "
            f"(eligible={match_run.candidate_counts.get('eligible_after_filters', 0)})"
        )

        match_run_path = output_dir / "match_run_07a.json"
        with open(match_run_path, "w") as f:
            json.dump(match_run.to_dict(), f, indent=2)
        outputs["match_run"] = str(match_run_path)

        explanations_path = output_dir / "match_explanations_07a.json"
        with open(explanations_path, "w") as f:
            json.dump({
                "deal_id": deal.deal_id,
                "generated_at": datetime.utcnow().isoformat(),
                "results": [
                    {
                        "rank": inv.get("rank"),
                        "investor": inv.get("full_name"),
                        "firm": inv.get("firm"),
                        "match_segment": inv.get("match_segment"),
                        "score_breakdown": inv.get("score_breakdown"),
                        "match_features": inv.get("match_features"),
                        "match_explanation": inv.get("match_explanation"),
                        "recent_signals": inv.get("recent_signals", []),
                    }
                    for inv in investors
                ],
            }, f, indent=2)
        outputs["match_explanations"] = str(explanations_path)
    except Exception as e:
        errors.append(f"Hybrid investor matching failed: {e}")
        logger.error(f"[{deal.deal_id}] Hybrid investor matching error: {e}")
        investors = []

    # ── Enrich contacts via Apollo ─────────────────────────────────────────────
    enriched_investors = []
    flagged_contacts = []

    for investor in investors:
        name = investor.get("full_name", "Unknown")
        firm = investor.get("firm", "Unknown")
        try:
            enriched = apollo.enrich_contact(name, firm)
            # Merge enriched data into investor record
            investor.update({
                "email": enriched.get("email") or investor.get("email", ""),
                "phone": enriched.get("phone") or investor.get("phone", ""),
                "linkedin_url": enriched.get("linkedin") or investor.get("linkedin_url", ""),
                "twitter_handle": enriched.get("twitter") or investor.get("twitter_handle", ""),
                "website": enriched.get("website") or investor.get("website", ""),
                "enriched_at": datetime.utcnow().isoformat(),
            })
        except Exception as e:
            errors.append(f"Apollo enrichment failed for {name}: {e}")
            logger.warning(f"[{deal.deal_id}] Apollo enrichment failed for {name}: {e}")

        # Validate — flag missing email or LinkedIn
        missing_fields = []
        if not investor.get("email"):
            missing_fields.append("email")
        if not investor.get("linkedin_url"):
            missing_fields.append("linkedin_url")

        if missing_fields:
            flagged_contacts.append({
                "investor": name,
                "firm": firm,
                "missing_fields": missing_fields,
            })
            investor["validation_flags"] = missing_fields
        else:
            investor["validation_flags"] = []

        enriched_investors.append(investor)

    if flagged_contacts:
        human_actions.append(
            f"{len(flagged_contacts)} investors have missing contact data — "
            f"manual research required: {[f['investor'] for f in flagged_contacts]}"
        )
        logger.warning(f"[{deal.deal_id}] {len(flagged_contacts)} contacts have missing data")

    # Handle < 20 results
    if len(enriched_investors) < 20:
        human_actions.append(
            f"Only {len(enriched_investors)} investors found (target: 20). "
            f"Consider manual research to supplement the list."
        )

    # ── Save outputs ──────────────────────────────────────────────────────────
    if enriched_investors:
        # JSON
        json_path = output_dir / "investor_list.json"
        with open(json_path, "w") as f:
            json.dump({
                "deal_id": deal.deal_id,
                "generated_at": datetime.utcnow().isoformat(),
                "matching_engine": {
                    "strategy": "hybrid_matching_v1",
                    "components": [
                        "structured_eligibility_filters",
                        "vector_retrieval_multi_namespace",
                        "keyword_overlap",
                        "weighted_reranker",
                        "explainability_layer",
                        "human_approval_queue",
                    ],
                },
                "count": len(enriched_investors),
                "investors": enriched_investors,
            }, f, indent=2)
        outputs["investor_list"] = str(json_path)

        # CSV
        csv_path = output_dir / "investor_contacts_enriched.csv"
        _write_investor_csv(enriched_investors, csv_path)
        outputs["investor_csv"] = str(csv_path)

        logger.info(
            f"[{deal.deal_id}] {len(enriched_investors)} investors saved → {json_path}"
        )

    human_actions.append(
        "⚠️ REVIEW REQUIRED: Review investor_list.json and match_explanations_07a.json; approve investor list before outreach begins."
    )
    human_actions.append(
        "Phil/team approval queue: apply exclusions, rank overrides, pinned investors, and do-not-contact flags before Step 7b."
    )

    deal.log_step("07a", "completed", f"Found and enriched {len(enriched_investors)} investors.", outputs)

    return deal, {
        "success": len(enriched_investors) > 0,
        "output": outputs,
        "errors": errors,
        "human_actions_required": human_actions,
    }


def _write_investor_csv(investors: list, path) -> None:
    """Write enriched investor list to CSV."""
    fieldnames = [
        "rank", "full_name", "firm", "title", "email", "phone",
        "linkedin_url", "twitter_handle", "website",
        "fit_score", "why_good_fit", "check_size_range",
        "investment_thesis", "validation_flags",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for inv in investors:
            inv_copy = dict(inv)
            inv_copy["validation_flags"] = ", ".join(inv_copy.get("validation_flags", []))
            writer.writerow(inv_copy)
