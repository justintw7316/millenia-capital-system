"""
modules/step_02_data_room.py — Step 2: Data Room

Box folder setup, document audit, tear sheet + pitch deck generation, Sequoia review.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Tuple

from core.deal import Deal, DocumentStatus
from core.logger import get_logger
from agents.document_agent import DocumentAgent
from integrations.box_client import BoxClient
from config import OUTPUT_DIR
from matching import build_company_profile_artifacts

logger = get_logger(__name__)


def run(deal: Deal, config: dict) -> Tuple[Deal, dict]:
    """
    Step 2: Data room setup, document audit, AI document generation, and Sequoia review.
    """
    logger.info(f"[{deal.deal_id}] ▶ Step 2: Data Room")

    errors = []
    human_actions = []
    outputs = {}

    output_dir = OUTPUT_DIR / deal.deal_id
    output_dir.mkdir(parents=True, exist_ok=True)

    box = BoxClient()
    agent = DocumentAgent()

    # ── Box folder setup ──────────────────────────────────────────────────────
    try:
        folder_id = box.check_folder(deal.company_name)
        if not folder_id:
            folder_id = box.create_folder(deal.company_name)
            logger.info(f"[{deal.deal_id}] Created Box folder: {folder_id}")
        deal.box_folder_id = folder_id
        outputs["box_folder_id"] = folder_id
        outputs["box_folder_url"] = box.get_folder_url(folder_id)
        logger.info(f"[{deal.deal_id}] Box folder ready: {folder_id}")
    except Exception as e:
        errors.append(f"Box API error: {e} — skipping Box, running document generation only.")
        logger.warning(f"[{deal.deal_id}] Box error (continuing): {e}")

    # ── Document audit ────────────────────────────────────────────────────────
    missing_docs = deal.documents.missing_documents()
    audit = {
        "deal_id": deal.deal_id,
        "company_name": deal.company_name,
        "audited_at": datetime.utcnow().isoformat(),
        "document_status": deal.documents.to_dict(),
        "missing_documents": missing_docs,
        "human_actions_required": [],
    }

    # Flag each missing document with instructions
    doc_instructions = {
        "tear_sheet": "Create 1-2 page investor tear sheet. AI draft will be generated — send to Abby for design.",
        "pitch_deck": "Build 11-slide pitch deck using provided outline. Send to Abby for design.",
        "financial_projections": "Provide 3-5 year financial projections including FCFF, WACC, Income Statement, Balance Sheet.",
        "nda": "Execute NDA with Millenia Ventures. Required before pitch deck distribution.",
        "ppm": "Prepare Private Placement Memorandum with Dock Walls.",
        "subscription_agreement": "Prepare Subscription Agreement with Dock Walls.",
        "wiring_instructions": "Provide bank wiring instructions for investor commitments.",
        "use_of_funds": "Provide detailed Use of Funds breakdown for the raise amount.",
    }

    for doc in missing_docs:
        instruction = doc_instructions.get(doc, f"Provide {doc.replace('_', ' ')}.")
        audit["human_actions_required"].append({
            "document": doc,
            "instruction": instruction,
            "priority": "high" if doc in ["tear_sheet", "nda"] else "medium",
        })
        human_actions.append(f"MISSING DOCUMENT — {doc}: {instruction}")

    # Save audit
    audit_path = output_dir / "data_room_audit.json"
    with open(audit_path, "w") as f:
        json.dump(audit, f, indent=2)
    outputs["audit_file"] = str(audit_path)

    # ── Generate tear sheet draft if missing ─────────────────────────────────
    if deal.documents.tear_sheet == DocumentStatus.MISSING:
        try:
            tear_sheet_md = agent.generate_tear_sheet_outline(deal)
            tear_sheet_path = output_dir / "tear_sheet_draft.md"
            tear_sheet_path.write_text(tear_sheet_md)
            outputs["tear_sheet_draft"] = str(tear_sheet_path)
            deal.documents.tear_sheet = DocumentStatus.DRAFT
            human_actions.append("Tear sheet AI draft generated — review and send to Abby for design.")
            logger.info(f"[{deal.deal_id}] Tear sheet draft saved → {tear_sheet_path}")
        except Exception as e:
            errors.append(f"Tear sheet generation failed: {e}")
            logger.error(f"[{deal.deal_id}] Tear sheet generation error: {e}")

    # ── Generate pitch deck outline if missing ────────────────────────────────
    if deal.documents.pitch_deck == DocumentStatus.MISSING:
        try:
            pitch_deck_data = agent.generate_pitch_deck_outline(deal)
            pitch_deck_path = output_dir / "pitch_deck_outline.json"
            with open(pitch_deck_path, "w") as f:
                json.dump(pitch_deck_data, f, indent=2)

            # Also write a human-readable markdown version
            md_path = output_dir / "pitch_deck_outline.md"
            _write_pitch_deck_md(pitch_deck_data, md_path)

            outputs["pitch_deck_outline"] = str(pitch_deck_path)
            deal.documents.pitch_deck = DocumentStatus.DRAFT
            human_actions.append(
                "Pitch deck 11-slide outline generated — send to Abby for design. "
                "Must NOT be distributed until NDA is approved."
            )
            logger.info(f"[{deal.deal_id}] Pitch deck outline saved → {pitch_deck_path}")
        except Exception as e:
            errors.append(f"Pitch deck generation failed: {e}")
            logger.error(f"[{deal.deal_id}] Pitch deck generation error: {e}")

    # ── NDA gate check ────────────────────────────────────────────────────────
    if deal.documents.nda != DocumentStatus.APPROVED:
        human_actions.append(
            "⚠️ NDA NOT APPROVED — Pitch deck must NOT be distributed until NDA is signed and approved."
        )

    # ── Sequoia review ────────────────────────────────────────────────────────
    try:
        review = agent.sequoia_review(deal)
        review_path = output_dir / "sequoia_review.json"
        with open(review_path, "w") as f:
            json.dump(review, f, indent=2)

        review_md_path = output_dir / "sequoia_review.md"
        _write_review_md(review, review_md_path, deal.company_name)

        outputs["sequoia_review"] = str(review_path)
        outputs["sequoia_review_md"] = str(review_md_path)

        overall_score = review.get("overall_score", 0)
        readiness = review.get("investment_readiness", "unknown")
        logger.info(
            f"[{deal.deal_id}] Sequoia review: score={overall_score}, readiness={readiness}"
        )

        if overall_score < 7:
            human_actions.append(
                f"Sequoia review score is {overall_score}/10 — "
                f"materials need significant revision before investor outreach."
            )

        # Financial review
        fin_review = agent.review_financials(deal)
        fin_path = output_dir / "financial_review.json"
        with open(fin_path, "w") as f:
            json.dump(fin_review, f, indent=2)
        outputs["financial_review"] = str(fin_path)

        missing_financials = fin_review.get("missing_items", [])
        if missing_financials:
            human_actions.append(
                f"Missing financial components: {', '.join(missing_financials)}. "
                f"Must be added before investor outreach."
            )

    except Exception as e:
        errors.append(f"Sequoia review failed: {e}")
        logger.error(f"[{deal.deal_id}] Sequoia review error: {e}")

    # ── Normalized company profile + embedding artifacts (for hybrid matching) ─
    try:
        matching_artifacts = build_company_profile_artifacts(deal)
        company_profile_path = output_dir / "company_profile_normalized.json"
        embeddings_path = output_dir / "company_profile_embeddings.json"
        vector_design_path = output_dir / "vector_db_design.json"

        with open(company_profile_path, "w") as f:
            json.dump(matching_artifacts["company_profile"], f, indent=2)
        with open(embeddings_path, "w") as f:
            json.dump({
                "deal_id": deal.deal_id,
                "embedding_model": matching_artifacts.get("embedding_model"),
                "generated_at": matching_artifacts.get("generated_at"),
                "embeddings": matching_artifacts.get("embeddings", {}),
            }, f, indent=2)
        with open(vector_design_path, "w") as f:
            json.dump(matching_artifacts.get("vector_db_design", {}), f, indent=2)

        outputs["company_profile_normalized"] = str(company_profile_path)
        outputs["company_profile_embeddings"] = str(embeddings_path)
        outputs["vector_db_design"] = str(vector_design_path)
        logger.info(f"[{deal.deal_id}] Matching artifacts saved → {company_profile_path}")
    except Exception as e:
        errors.append(f"Company profile/embedding artifact generation failed: {e}")
        logger.warning(f"[{deal.deal_id}] Matching artifact generation error: {e}")

    deal.log_step("02", "completed", f"Data room audited. Missing docs: {missing_docs}", outputs)

    return deal, {
        "success": len(errors) == 0,
        "output": outputs,
        "errors": errors,
        "human_actions_required": human_actions,
    }


def _write_pitch_deck_md(data: dict, path: Path) -> None:
    """Write a readable markdown version of the pitch deck outline."""
    lines = ["# Pitch Deck Outline\n"]
    for slide in data.get("slides", []):
        lines.append(f"## Slide {slide.get('slide_number', '')}: {slide.get('title', '')}\n")
        for point in slide.get("key_points", []):
            lines.append(f"- {point}")
        guidance = slide.get("content_guidance", "")
        if guidance:
            lines.append(f"\n*Guidance: {guidance}*")
        lines.append("")
    path.write_text("\n".join(lines))


def _write_review_md(review: dict, path: Path, company_name: str) -> None:
    """Write a readable markdown version of the Sequoia review."""
    lines = [f"# Sequoia Review — {company_name}\n"]
    lines.append(f"**Overall Score:** {review.get('overall_score', 0)}/10")
    lines.append(f"**Investment Readiness:** {review.get('investment_readiness', 'unknown')}\n")
    lines.append("## Section Grades\n")
    for section, data in review.get("grades", {}).items():
        score = data.get("score", 0)
        notes = data.get("notes", "")
        indicator = "✅" if score >= 8 else ("⚠️" if score >= 6 else "❌")
        lines.append(f"### {indicator} {section.replace('_', ' ').title()}: {score}/10")
        if notes:
            lines.append(f"{notes}\n")
    if review.get("critical_revisions"):
        lines.append("## Critical Revisions Required\n")
        for rev in review["critical_revisions"]:
            lines.append(f"- {rev}")
    if review.get("strengths"):
        lines.append("\n## Strengths\n")
        for s in review["strengths"]:
            lines.append(f"- {s}")
    path.write_text("\n".join(lines))
