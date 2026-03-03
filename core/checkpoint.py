"""
core/checkpoint.py — Saves/loads deal state to JSON so a crashed run can resume.

Checkpoint location: outputs/{deal_id}/checkpoint.json
"""
import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from core.deal import Deal
from core.logger import get_logger

logger = get_logger(__name__)


class CheckpointManager:
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)

    def _checkpoint_path(self, deal_id: str) -> Path:
        return self.output_dir / deal_id / "checkpoint.json"

    def save(self, deal: Deal, completed_step: str) -> None:
        """
        Persist deal state after a step completes.

        Args:
            deal: Current Deal object.
            completed_step: The step identifier just completed (e.g. "02", "07a").
        """
        path = self._checkpoint_path(deal.deal_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint_data = {
            "deal_id": deal.deal_id,
            "completed_step": completed_step,
            "saved_at": datetime.utcnow().isoformat(),
            "deal_state": deal.to_dict(),
        }

        with open(path, "w") as f:
            json.dump(checkpoint_data, f, indent=2, default=str)

        logger.debug(f"[{deal.deal_id}] Checkpoint saved after step {completed_step} → {path}")

    def load(self, deal_id: str) -> Optional[Deal]:
        """
        Load and reconstruct a Deal from the checkpoint file.

        Returns:
            Deal object if checkpoint exists, None otherwise.
        """
        path = self._checkpoint_path(deal_id)
        if not path.exists():
            logger.debug(f"[{deal_id}] No checkpoint found at {path}")
            return None

        with open(path, "r") as f:
            checkpoint_data = json.load(f)

        deal = Deal.from_dict(checkpoint_data["deal_state"])
        logger.info(
            f"[{deal_id}] Checkpoint loaded — last completed step: "
            f"{checkpoint_data.get('completed_step')} (saved at {checkpoint_data.get('saved_at')})"
        )
        return deal

    def get_last_completed_step(self, deal_id: str) -> Optional[str]:
        """
        Returns the last completed step identifier from the checkpoint, or None.
        """
        path = self._checkpoint_path(deal_id)
        if not path.exists():
            return None

        with open(path, "r") as f:
            data = json.load(f)

        return data.get("completed_step")

    def clear(self, deal_id: str) -> None:
        """
        Delete the checkpoint file for a deal (fresh restart).
        """
        path = self._checkpoint_path(deal_id)
        if path.exists():
            path.unlink()
            logger.info(f"[{deal_id}] Checkpoint cleared.")
        else:
            logger.debug(f"[{deal_id}] No checkpoint to clear.")

    def exists(self, deal_id: str) -> bool:
        """Returns True if a checkpoint exists for this deal."""
        return self._checkpoint_path(deal_id).exists()
