"""
core/workflow_engine.py — Orchestrates step execution across the full pipeline.

Handles:
- Sequential step execution
- Per-step failure handling (non-blocking by default, critical gates block)
- Checkpoint save/resume
- Status reporting
"""
import importlib
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from core.deal import Deal
from core.checkpoint import CheckpointManager
from core.logger import get_logger
from config import STEP_ORDER, CRITICAL_GATE_STEPS, OUTPUT_DIR

logger = get_logger(__name__)

# Map step IDs to module paths
_STEP_MODULE_MAP = {
    "01": "modules.step_01_timeline",
    "02": "modules.step_02_data_room",
    "03": "modules.step_03_alt_funding",
    "04": "modules.step_04_founder_video",
    "05": "modules.step_05_founder_interview",
    "06": "modules.step_06_gt_securities",
    "07a": "modules.step_07a_investor_discovery",
    "07b": "modules.step_07b_outreach_messages",
    "07c": "modules.step_07c_meetalfred_campaign",
    "08": "modules.step_08_followup_campaign",
    "09": "modules.step_09_launch_campaigns",
    "10": "modules.step_10_pr_visibility",
    "11": "modules.step_11_funnels_vetting",
    "12": "modules.step_12_traditional_outreach",
    "13": "modules.step_13_pitch_events",
    "14": "modules.step_14_reporting",
}

_STEP_NAMES = {
    "01": "Timeline & Metrics",
    "02": "Data Room",
    "03": "Alternative Funding Sources",
    "04": "Founder Video",
    "05": "Founder Interview",
    "06": "GT Securities (Human)",
    "07a": "Investor Discovery",
    "07b": "Outreach Messages",
    "07c": "MeetAlfred Campaign",
    "08": "Follow-Up Campaign",
    "09": "Launch Campaigns",
    "10": "PR & Visibility",
    "11": "Funnels & Investor Vetting",
    "12": "Traditional Outreach",
    "13": "Pitch Events",
    "14": "Reporting & Compliance",
}


class WorkflowEngine:
    """
    Orchestrates the 14-step Capital Formation pipeline for a single deal.
    """

    def __init__(self, output_dir: str = None):
        self.output_dir = str(output_dir or OUTPUT_DIR)
        self.checkpoint_manager = CheckpointManager(self.output_dir)
        self._config = {"output_dir": self.output_dir}

    # ── Public API ─────────────────────────────────────────────────────────────

    def run_full_pipeline(self, deal: Deal) -> Deal:
        """
        Execute all steps in order (01 → 14).

        On any non-critical failure: log, save checkpoint, and continue.
        On critical gate failure: pause and return with error state.

        Args:
            deal: Deal object to process.

        Returns:
            Updated Deal object after all steps.
        """
        logger.info(
            f"[{deal.deal_id}] ════ STARTING FULL PIPELINE — {deal.company_name} ════"
        )
        return self._run_steps(deal, STEP_ORDER)

    def run_step(self, deal: Deal, step_number: str) -> Tuple[Deal, dict]:
        """
        Execute a single step by its identifier.

        Args:
            deal: Current Deal object.
            step_number: Step ID (e.g., "02", "07a").

        Returns:
            Tuple of (updated Deal, result dict).
        """
        step = step_number.lower().strip()
        if step not in _STEP_MODULE_MAP:
            raise ValueError(
                f"Unknown step: '{step_number}'. Valid steps: {list(_STEP_MODULE_MAP.keys())}"
            )
        deal, result = self._execute_step(deal, step)
        self.checkpoint_manager.save(deal, step)
        return deal, result

    def run_from_step(self, deal: Deal, start_step: str) -> Deal:
        """
        Execute all steps from start_step to the end of the pipeline.

        Useful for resuming after a crash or re-running from a specific point.

        Args:
            deal: Current Deal object (can be loaded from checkpoint).
            start_step: Step ID to start from (e.g., "03").

        Returns:
            Updated Deal object.
        """
        start = start_step.lower().strip()
        if start not in STEP_ORDER:
            raise ValueError(f"Unknown start step: '{start_step}'")

        start_idx = STEP_ORDER.index(start)
        remaining_steps = STEP_ORDER[start_idx:]
        logger.info(
            f"[{deal.deal_id}] Resuming from step {start} — "
            f"{len(remaining_steps)} steps remaining"
        )
        return self._run_steps(deal, remaining_steps)

    def get_status_report(self, deal: Deal) -> Dict:
        """
        Generate a structured status report for a deal.

        Args:
            deal: Current Deal object.

        Returns:
            Dict with pipeline status, step completion, and key metrics.
        """
        completed_steps = {
            entry["step"] for entry in deal.step_log if entry.get("status") == "completed"
        }
        blocked_steps = {
            entry["step"] for entry in deal.step_log if entry.get("status") == "blocked"
        }
        skipped_steps = {
            entry["step"] for entry in deal.step_log if entry.get("status") == "skipped"
        }

        step_status = {}
        for step in STEP_ORDER:
            if step in completed_steps:
                status = "completed"
            elif step in blocked_steps:
                status = "blocked"
            elif step in skipped_steps:
                status = "skipped"
            else:
                status = "pending"
            step_status[step] = {
                "name": _STEP_NAMES.get(step, step),
                "status": status,
            }

        # Checkpoint info
        last_completed = self.checkpoint_manager.get_last_completed_step(deal.deal_id)

        # Key metrics
        contacted = len(deal.investors_contacted)
        responded = len(deal.investors_responded)
        committed = len(deal.investors_committed)
        response_rate = (responded / contacted) if contacted > 0 else 0.0
        total_committed = sum(
            inv.get("commitment_amount", 0) for inv in deal.investors_committed
        )

        return {
            "deal_id": deal.deal_id,
            "company_name": deal.company_name,
            "raise_amount": deal.raise_amount,
            "stage": deal.stage.value,
            "generated_at": datetime.utcnow().isoformat(),
            "pipeline": step_status,
            "last_checkpoint": last_completed,
            "metrics": {
                "investors_contacted": contacted,
                "investors_responded": responded,
                "investors_committed": committed,
                "response_rate_percent": round(response_rate * 100, 1),
                "total_committed_usd": total_committed,
                "raise_target_usd": deal.raise_amount,
                "percent_raised": round(total_committed / deal.raise_amount * 100, 1) if deal.raise_amount else 0,
                "outreach_week": deal.outreach_week,
                "campaign_active": deal.campaign_active,
            },
            "errors": deal.errors,
            "open_issues": _count_human_actions(deal),
        }

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _run_steps(self, deal: Deal, steps: List[str]) -> Deal:
        """Execute a list of steps in order."""
        for step in steps:
            try:
                deal, result = self._execute_step(deal, step)
                self.checkpoint_manager.save(deal, step)

                # Critical gate: step 02 must succeed before 07a
                if step in CRITICAL_GATE_STEPS and not result.get("success"):
                    logger.error(
                        f"[{deal.deal_id}] ⛔ Critical gate failed at step {step} — "
                        f"pipeline paused. Resolve issues and resume."
                    )
                    deal.add_error(f"Pipeline paused at critical gate: step {step}")
                    break

            except Exception as e:
                tb = traceback.format_exc()
                error_msg = f"Step {step} raised an unexpected exception: {e}"
                logger.error(f"[{deal.deal_id}] {error_msg}\n{tb}")
                deal.add_error(error_msg)
                deal.log_step(step, "failed", error_msg)
                self.checkpoint_manager.save(deal, f"{step}_failed")
                # Non-blocking: continue to next step

        logger.info(f"[{deal.deal_id}] Pipeline run complete.")
        return deal

    def _execute_step(self, deal: Deal, step: str) -> Tuple[Deal, dict]:
        """
        Load and run a single step module.

        Args:
            deal: Current Deal object.
            step: Step identifier.

        Returns:
            Tuple of (updated Deal, result dict).
        """
        module_path = _STEP_MODULE_MAP[step]
        step_name = _STEP_NAMES.get(step, step)

        logger.info(f"[{deal.deal_id}] ── Step {step}: {step_name} ──")
        start_time = datetime.utcnow()

        try:
            module = importlib.import_module(module_path)
            deal, result = module.run(deal, self._config)
        except ModuleNotFoundError:
            error = f"Step module not found: {module_path}"
            logger.error(f"[{deal.deal_id}] {error}")
            result = {"success": False, "output": {}, "errors": [error], "human_actions_required": []}
            deal.log_step(step, "failed", error)
            return deal, result

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        status = "completed" if result.get("success") else "failed"

        # Log human actions if any
        human_actions = result.get("human_actions_required", [])
        if human_actions:
            logger.info(
                f"[{deal.deal_id}] Step {step} — {len(human_actions)} human action(s) required"
            )
            for action in human_actions:
                logger.warning(f"  ⚡ HUMAN ACTION: {action}")

        # Log errors
        for err in result.get("errors", []):
            logger.warning(f"[{deal.deal_id}] Step {step} error: {err}")

        logger.info(
            f"[{deal.deal_id}] Step {step} {status.upper()} in {elapsed:.1f}s"
        )
        return deal, result


def _count_human_actions(deal: Deal) -> int:
    """Count total human action items logged across all steps."""
    # Simplified — in production this would read from a dedicated field
    return len([e for e in deal.step_log if e.get("status") in ("blocked", "failed")])
