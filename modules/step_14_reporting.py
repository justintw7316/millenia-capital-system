"""
modules/step_14_reporting.py — Step 14: Reporting, Compliance & Transfers

Weekly reports, wire verification, legal tracking. Runs every 7 days.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Tuple

from core.deal import Deal
from core.logger import get_logger
from agents.reporting_agent import ReportingAgent
from config import OUTPUT_DIR

logger = get_logger(__name__)


def run(deal: Deal, config: dict) -> Tuple[Deal, dict]:
    """
    Step 14: Generate weekly report, wire verification checklist, and legal tracking log.

    This step runs every 7 days regardless of other step status.
    """
    week = deal.outreach_week or 1
    logger.info(f"[{deal.deal_id}] ▶ Step 14: Reporting — Week {week}")

    errors = []
    human_actions = []
    outputs = {}

    # ── Set up output directory ───────────────────────────────────────────────
    output_dir = OUTPUT_DIR / deal.deal_id
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    agent = ReportingAgent()

    # ── Weekly progress report ────────────────────────────────────────────────
    try:
        report_md = agent.generate_weekly_report(deal)
        report_path = reports_dir / f"week_{week:02d}_report.md"
        report_path.write_text(report_md)
        outputs["weekly_report"] = str(report_path)
        logger.info(f"[{deal.deal_id}] Week {week} report saved → {report_path}")

        # Check for embedded alerts (Phil alerts)
        if "PHIL ALERT" in report_md:
            human_actions.append(
                "⚠️ PHIL ALERT in weekly report — review immediately. See reports directory."
            )
    except Exception as e:
        errors.append(f"Weekly report generation failed: {e}")
        logger.error(f"[{deal.deal_id}] Report error: {e}")

    # ── Wire/ACH verification checklist ──────────────────────────────────────
    wire_checklist = _generate_wire_checklist(deal, week)
    wire_path = output_dir / "wire_verification_checklist.md"
    wire_path.write_text(wire_checklist)
    outputs["wire_verification"] = str(wire_path)

    # ── Legal document tracking log ───────────────────────────────────────────
    try:
        compliance = agent.generate_compliance_log(deal)
        compliance_path = reports_dir / f"week_{week:02d}_compliance.json"
        with open(compliance_path, "w") as f:
            json.dump(compliance, f, indent=2)

        # Markdown version
        compliance_md_path = output_dir / "legal_tracking_log.md"
        compliance_md_path.write_text(compliance.get("compliance_log", ""))
        outputs["legal_tracking"] = str(compliance_md_path)
        outputs["compliance_json"] = str(compliance_path)

        # Flag Dock Walls items
        dock_walls_items = compliance.get("action_items_for_dock_walls", [])
        if dock_walls_items:
            human_actions.append(
                f"FLAG FOR DOCK WALLS: {len(dock_walls_items)} legal items require attention: "
                f"{'; '.join(dock_walls_items)}"
            )
    except Exception as e:
        errors.append(f"Compliance log generation failed: {e}")
        logger.error(f"[{deal.deal_id}] Compliance log error: {e}")

    # ── Response rate analysis ────────────────────────────────────────────────
    response_rate = agent.calculate_response_rate(deal)
    meeting_conversion = agent.calculate_meeting_conversion(deal)
    total_committed = sum(inv.get("commitment_amount", 0) for inv in deal.investors_committed)

    # Save weekly metrics snapshot
    metrics = {
        "week": week,
        "timestamp": datetime.utcnow().isoformat(),
        "investors_contacted": len(deal.investors_contacted),
        "investors_responded": len(deal.investors_responded),
        "investors_committed": len(deal.investors_committed),
        "response_rate": response_rate,
        "meeting_conversion": meeting_conversion,
        "total_committed_usd": total_committed,
        "raise_target_usd": deal.raise_amount,
        "percent_raised": (total_committed / deal.raise_amount * 100) if deal.raise_amount else 0,
    }
    metrics_path = reports_dir / f"week_{week:02d}_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    outputs["metrics"] = str(metrics_path)

    # ── Hybrid matching performance snapshots (score deciles / segments) ────
    try:
        investor_list_path = output_dir / "investor_list.json"
        if investor_list_path.exists():
            with open(investor_list_path, "r") as f:
                investor_payload = json.load(f)
            match_investors = investor_payload.get("investors", [])
            if match_investors:
                responded_emails = {i.get("email", "").lower() for i in deal.investors_responded}
                committed_emails = {i.get("email", "").lower() for i in deal.investors_committed}
                scored = []
                for inv in match_investors:
                    score = inv.get("fit_score")
                    if score is None:
                        continue
                    email = (inv.get("email") or "").lower()
                    scored.append({
                        "email": email,
                        "score": float(score),
                        "segment": inv.get("match_segment", "unknown"),
                        "responded": email in responded_emails if email else False,
                        "committed": email in committed_emails if email else False,
                    })
                scored.sort(key=lambda x: x["score"], reverse=True)
                if scored:
                    deciles = []
                    bucket_size = max(1, len(scored) // 10)
                    for idx in range(10):
                        chunk = scored[idx * bucket_size:(idx + 1) * bucket_size] if idx < 9 else scored[idx * bucket_size:]
                        if not chunk:
                            continue
                        deciles.append({
                            "decile": idx + 1,
                            "score_min": min(c["score"] for c in chunk),
                            "score_max": max(c["score"] for c in chunk),
                            "count": len(chunk),
                            "reply_rate": round(sum(1 for c in chunk if c["responded"]) / len(chunk), 3),
                            "commit_rate": round(sum(1 for c in chunk if c["committed"]) / len(chunk), 3),
                        })
                    segments = {}
                    for row in scored:
                        seg = row["segment"]
                        segments.setdefault(seg, {"count": 0, "responded": 0, "committed": 0})
                        segments[seg]["count"] += 1
                        segments[seg]["responded"] += int(row["responded"])
                        segments[seg]["committed"] += int(row["committed"])
                    for seg, agg in segments.items():
                        agg["reply_rate"] = round(agg["responded"] / agg["count"], 3) if agg["count"] else 0.0
                        agg["commit_rate"] = round(agg["committed"] / agg["count"], 3) if agg["count"] else 0.0

                    matching_perf_path = reports_dir / f"week_{week:02d}_matching_performance.json"
                    with open(matching_perf_path, "w") as f:
                        json.dump({
                            "deal_id": deal.deal_id,
                            "week": week,
                            "generated_at": datetime.utcnow().isoformat(),
                            "metrics_tracked": [
                                "reply_rate_by_score_decile",
                                "commit_rate_by_score_decile",
                                "conversion_by_match_segment",
                            ],
                            "deciles": deciles,
                            "segments": segments,
                        }, f, indent=2)
                    outputs["matching_performance"] = str(matching_perf_path)
    except Exception as e:
        errors.append(f"Matching performance snapshot failed: {e}")
        logger.warning(f"[{deal.deal_id}] Matching performance metrics error: {e}")

    human_actions.extend([
        "Distribute weekly report to Phil, Das, and relevant team members.",
        "Wire/ACH: All transfers require dual confirmation from client AND investor.",
        "Legal: Review legal_tracking_log.md and ensure Dock Walls has reviewed all flagged items.",
    ])

    deal.log_step("14", "completed", f"Week {week} report generated. Response rate: {response_rate:.1%}", outputs)

    return deal, {
        "success": len(errors) == 0,
        "output": outputs,
        "errors": errors,
        "human_actions_required": human_actions,
    }


def _generate_wire_checklist(deal: Deal, week: int) -> str:
    committed_count = len(deal.investors_committed)
    total_committed = sum(inv.get("commitment_amount", 0) for inv in deal.investors_committed)

    return f"""# Wire/ACH Verification Checklist — {deal.company_name}

**Week:** {week}
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d')}

**⚠️ CRITICAL: All wire transfers require DUAL CONFIRMATION from both client AND investor.**

---

## Current Commitments

| Investor | Committed Amount | Wire Status | Confirmed by Client | Confirmed by Investor |
|----------|-----------------|-------------|--------------------|-----------------------|
{chr(10).join(f"| {inv.get('name', 'Unknown')} | ${inv.get('commitment_amount', 0):,.0f} | Pending | [ ] | [ ] |" for inv in deal.investors_committed) or "| No commitments yet | — | — | — | — |"}

**Total Committed:** ${total_committed:,.0f} of ${deal.raise_amount:,.0f} target ({total_committed/deal.raise_amount*100:.1f}%)

---

## Wire Transfer Process

### Step 1 — Investor Commitment
- [ ] Investor signed Subscription Agreement
- [ ] Investor confirmed accredited investor status
- [ ] NDA executed and approved
- [ ] Investment terms reviewed by Dock Walls

### Step 2 — Wire Instructions
- [ ] Provide investor with official wiring instructions (do NOT share informally)
- [ ] Instructions must come from official Millenia Ventures / law firm email
- [ ] Investor confirms receipt of instructions

### Step 3 — Client Confirmation
- [ ] Client (founder) confirms wiring instructions are correct
- [ ] Client confirms bank account details
- [ ] Client signs off on specific transfer amount

### Step 4 — Investor Confirmation
- [ ] Investor initiates wire transfer
- [ ] Investor provides wire confirmation number
- [ ] Investor confirms bank and routing details match

### Step 5 — Receipt Confirmation
- [ ] Confirm funds received in escrow/company account
- [ ] Send confirmation to investor
- [ ] Update investor record in system
- [ ] Notify Philip and Millenia Ventures team

---

## Anti-Fraud Checklist
- [ ] Never accept wire instruction changes via email without phone verification
- [ ] Always call investor directly to verify large transfers (> $50K)
- [ ] Verify wire routing numbers independently before confirming
- [ ] Document all wire-related communications in legal tracking log

---

## Contact for Wire Issues
- **Primary:** [Dock Walls representative contact]
- **Secondary:** Philip at Millenia Ventures
- **Escalation:** [Law firm name and contact]

---
*All wire transfers are subject to applicable securities law and firm compliance requirements.*
"""
