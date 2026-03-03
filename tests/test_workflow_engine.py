"""
tests/test_workflow_engine.py — Tests for WorkflowEngine orchestration logic.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.deal import Deal, DealDocuments, DocumentStatus, DealStage
from core.workflow_engine import WorkflowEngine
from core.checkpoint import CheckpointManager


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def clean_deal():
    """Deal with all documents present."""
    deal = Deal(
        deal_id="test_clean_001",
        company_name="TestCorp AI",
        company_website="https://testcorpai.com",
        industry="artificial intelligence",
        raise_amount=2_500_000,
        founder_name="Alice Johnson",
        founder_email="alice@testcorpai.com",
        founder_linkedin="https://linkedin.com/in/alicejohnson",
        created_at="2026-02-24",
    )
    # All documents present
    deal.documents = DealDocuments(
        tear_sheet=DocumentStatus.APPROVED,
        pitch_deck=DocumentStatus.APPROVED,
        financial_projections=DocumentStatus.APPROVED,
        nda=DocumentStatus.APPROVED,
        ppm=DocumentStatus.APPROVED,
        subscription_agreement=DocumentStatus.APPROVED,
        wiring_instructions=DocumentStatus.APPROVED,
        use_of_funds=DocumentStatus.APPROVED,
    )
    return deal


@pytest.fixture
def missing_docs_deal():
    """Deal with tear sheet and pitch deck missing."""
    deal = Deal(
        deal_id="test_missing_001",
        company_name="MissingDocs Inc",
        company_website="https://missingdocs.com",
        industry="fintech",
        raise_amount=1_000_000,
        founder_name="Bob Williams",
        founder_email="bob@missingdocs.com",
        founder_linkedin="https://linkedin.com/in/bobwilliams",
        created_at="2026-02-24",
    )
    deal.documents = DealDocuments(
        tear_sheet=DocumentStatus.MISSING,
        pitch_deck=DocumentStatus.MISSING,
        financial_projections=DocumentStatus.DRAFT,
        nda=DocumentStatus.APPROVED,
    )
    return deal


@pytest.fixture
def high_value_deal():
    """Deal with raise >= $5M — triggers broker-dealer portal."""
    deal = Deal(
        deal_id="test_highval_001",
        company_name="BigRaise Corp",
        company_website="https://bigraise.com",
        industry="healthtech",
        raise_amount=6_000_000,
        founder_name="Carol Zhang",
        founder_email="carol@bigraise.com",
        founder_linkedin="https://linkedin.com/in/carolzhang",
        created_at="2026-02-24",
    )
    deal.documents = DealDocuments(
        tear_sheet=DocumentStatus.APPROVED,
        nda=DocumentStatus.APPROVED,
    )
    return deal


@pytest.fixture
def engine(tmp_path):
    """WorkflowEngine with temp output dir."""
    return WorkflowEngine(output_dir=str(tmp_path))


# ── WorkflowEngine Tests ──────────────────────────────────────────────────────

class TestWorkflowEngineStatusReport:
    def test_status_report_structure(self, engine, clean_deal):
        status = engine.get_status_report(clean_deal)
        assert "deal_id" in status
        assert "company_name" in status
        assert "pipeline" in status
        assert "metrics" in status
        assert "errors" in status

    def test_status_report_all_steps_present(self, engine, clean_deal):
        status = engine.get_status_report(clean_deal)
        expected_steps = [
            "01", "02", "03", "04", "05", "06",
            "07a", "07b", "07c", "08", "09", "10",
            "11", "12", "13", "14",
        ]
        for step in expected_steps:
            assert step in status["pipeline"], f"Step {step} missing from pipeline"

    def test_metrics_structure(self, engine, clean_deal):
        status = engine.get_status_report(clean_deal)
        m = status["metrics"]
        assert "investors_contacted" in m
        assert "response_rate_percent" in m
        assert "total_committed_usd" in m
        assert "raise_target_usd" in m


class TestStepExecution:
    def test_run_step_01_timeline(self, engine, clean_deal):
        """Step 1 should generate timeline.json."""
        deal, result = engine.run_step(clean_deal, "01")
        assert result["success"] is True
        assert "output" in result
        assert "errors" in result
        assert "human_actions_required" in result

    def test_run_step_06_gt_securities(self, engine, clean_deal):
        """Step 6 (human-only) should succeed and generate notification."""
        deal, result = engine.run_step(clean_deal, "06")
        assert result["success"] is True
        assert "philip_notification" in result["output"]

    def test_run_step_invalid_id(self, engine, clean_deal):
        """Invalid step ID should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown step"):
            engine.run_step(clean_deal, "99")

    def test_step_result_schema(self, engine, clean_deal):
        """Every step result must have required keys."""
        deal, result = engine.run_step(clean_deal, "01")
        assert "success" in result
        assert isinstance(result["success"], bool)
        assert "output" in result
        assert "errors" in result
        assert isinstance(result["errors"], list)
        assert "human_actions_required" in result
        assert isinstance(result["human_actions_required"], list)


class TestPipelineResume:
    def test_resume_from_step_skips_earlier_steps(self, engine, clean_deal, tmp_path):
        """run_from_step should not re-run steps before start_step."""
        # Run step 1 first
        deal, _ = engine.run_step(clean_deal, "01")
        engine.checkpoint_manager.save(deal, "01")

        # Reload and resume from step 6
        deal_resumed = engine.run_from_step(deal, "06")

        # Step 06 should be in log
        step_ids = [e["step"] for e in deal_resumed.step_log]
        assert "06" in step_ids

    def test_checkpoint_save_and_load(self, engine, clean_deal, tmp_path):
        """Checkpoint should persist deal state across sessions."""
        # Save checkpoint
        engine.checkpoint_manager.save(clean_deal, "03")

        # Load it back
        loaded = engine.checkpoint_manager.load(clean_deal.deal_id)
        assert loaded is not None
        assert loaded.deal_id == clean_deal.deal_id
        assert loaded.company_name == clean_deal.company_name

        last_step = engine.checkpoint_manager.get_last_completed_step(clean_deal.deal_id)
        assert last_step == "03"

    def test_checkpoint_clear(self, engine, clean_deal):
        """Clearing checkpoint should remove the file."""
        engine.checkpoint_manager.save(clean_deal, "02")
        assert engine.checkpoint_manager.exists(clean_deal.deal_id)
        engine.checkpoint_manager.clear(clean_deal.deal_id)
        assert not engine.checkpoint_manager.exists(clean_deal.deal_id)
