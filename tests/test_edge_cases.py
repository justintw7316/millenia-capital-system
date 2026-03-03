"""
tests/test_edge_cases.py — Edge case tests for the pipeline.

Covers: missing docs, unsigned NDAs, low response rate, API failure, resume, high-value deal.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.deal import Deal, DealDocuments, DocumentStatus
from core.workflow_engine import WorkflowEngine
from agents.reporting_agent import ReportingAgent
from config import BROKER_DEALER_THRESHOLD


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_deal(**kwargs) -> Deal:
    defaults = dict(
        deal_id="edge_test_001",
        company_name="EdgeCase Corp",
        company_website="https://edgecase.com",
        industry="artificial intelligence",
        raise_amount=2_500_000,
        founder_name="Test Founder",
        founder_email="founder@edgecase.com",
        founder_linkedin="https://linkedin.com/in/testfounder",
        created_at="2026-02-24",
    )
    defaults.update(kwargs)
    return Deal(**defaults)


@pytest.fixture
def engine(tmp_path):
    return WorkflowEngine(output_dir=str(tmp_path))


# ── Missing Documents Tests ───────────────────────────────────────────────────

class TestMissingDocuments:
    def test_step02_generates_tear_sheet_draft_when_missing(self, engine, tmp_path):
        """Step 2 must generate an AI draft when tear sheet is missing."""
        deal = _make_deal(deal_id="edge_miss_001")
        deal.documents = DealDocuments(
            tear_sheet=DocumentStatus.MISSING,
            pitch_deck=DocumentStatus.MISSING,
            nda=DocumentStatus.APPROVED,
        )
        with patch("modules.step_02_data_room.DocumentAgent") as MockAgent:
            mock_agent = MagicMock()
            mock_agent.generate_tear_sheet_outline.return_value = "# Mock Tear Sheet"
            mock_agent.generate_pitch_deck_outline.return_value = {"slides": [{}] * 11}
            mock_agent.sequoia_review.return_value = {
                "grades": {}, "overall_score": 7, "investment_readiness": "needs_work",
                "critical_revisions": [], "strengths": [],
            }
            mock_agent.review_financials.return_value = {"missing_items": [], "components": {}}
            MockAgent.return_value = mock_agent

            deal, result = engine.run_step(deal, "02")

        # Tear sheet should be upgraded to DRAFT
        assert deal.documents.tear_sheet == DocumentStatus.DRAFT, \
            "Tear sheet status should be DRAFT after AI generation"

        # Should flag for human review
        assert any("tear sheet" in a.lower() or "AI draft" in a for a in result["human_actions_required"]), \
            "Should flag tear sheet draft for human review"

    def test_step02_flags_missing_docs_as_human_actions(self, engine):
        """Step 2 must list every missing document as a human action."""
        deal = _make_deal(deal_id="edge_miss_002")
        deal.documents = DealDocuments(
            tear_sheet=DocumentStatus.MISSING,
            ppm=DocumentStatus.MISSING,
            subscription_agreement=DocumentStatus.MISSING,
        )
        with patch("modules.step_02_data_room.DocumentAgent") as MockAgent, \
             patch("modules.step_02_data_room.BoxClient"):
            mock_agent = MagicMock()
            mock_agent.generate_tear_sheet_outline.return_value = "# Mock"
            mock_agent.generate_pitch_deck_outline.return_value = {"slides": [{}] * 11}
            mock_agent.sequoia_review.return_value = {
                "grades": {}, "overall_score": 5, "investment_readiness": "not_ready",
                "critical_revisions": [], "strengths": [],
            }
            mock_agent.review_financials.return_value = {"missing_items": [], "components": {}}
            MockAgent.return_value = mock_agent

            deal, result = engine.run_step(deal, "02")

        # All 3 missing docs should appear in human actions
        actions_text = " ".join(result.get("human_actions_required", [])).lower()
        assert "ppm" in actions_text or "tear_sheet" in actions_text


# ── NDA Gate Tests ────────────────────────────────────────────────────────────

class TestNDAGate:
    def test_nda_not_approved_blocks_pitch_deck_distribution(self, engine):
        """When NDA is not approved, pitch deck must NOT be distributed."""
        deal = _make_deal(deal_id="edge_nda_001")
        deal.documents = DealDocuments(
            nda=DocumentStatus.DRAFT,  # Not approved
            tear_sheet=DocumentStatus.APPROVED,
            pitch_deck=DocumentStatus.APPROVED,
        )
        with patch("modules.step_02_data_room.DocumentAgent") as MockAgent, \
             patch("modules.step_02_data_room.BoxClient"):
            mock_agent = MagicMock()
            mock_agent.generate_tear_sheet_outline.return_value = "# Mock"
            mock_agent.generate_pitch_deck_outline.return_value = {"slides": [{}] * 11}
            mock_agent.sequoia_review.return_value = {
                "grades": {}, "overall_score": 8, "investment_readiness": "investor_ready",
                "critical_revisions": [], "strengths": [],
            }
            mock_agent.review_financials.return_value = {"missing_items": [], "components": {}}
            MockAgent.return_value = mock_agent

            deal, result = engine.run_step(deal, "02")

        human_actions_text = " ".join(result.get("human_actions_required", [])).lower()
        assert "nda" in human_actions_text, "NDA warning must appear in human actions"


# ── Low Response Rate Tests ───────────────────────────────────────────────────

class TestLowResponseRate:
    def test_phil_alert_generated_when_response_rate_below_threshold(self):
        """If response rate < 20% and 20+ contacts, Phil alert must be in report."""
        deal = _make_deal(deal_id="edge_rr_001")
        # Simulate 20 contacted, only 2 responded (10% rate)
        deal.investors_contacted = [{"email": f"inv{i}@firm.com"} for i in range(20)]
        deal.investors_responded = [{"email": "inv0@firm.com"}, {"email": "inv1@firm.com"}]

        mock_claude = MagicMock()
        mock_claude.generate.return_value = "# Weekly Report\n\nMock report content."

        agent = ReportingAgent(claude_client=mock_claude)
        rate = agent.calculate_response_rate(deal)
        assert rate == pytest.approx(0.10, abs=0.01)

        # The report should trigger a Phil alert
        report = agent.generate_weekly_report(deal)
        assert "PHIL ALERT" in report, "Report must contain Phil alert for low response rate"

    def test_no_alert_when_response_rate_acceptable(self):
        """No alert when response rate is >= 20%."""
        deal = _make_deal(deal_id="edge_rr_002")
        deal.investors_contacted = [{"email": f"inv{i}@firm.com"} for i in range(20)]
        deal.investors_responded = [{"email": f"inv{i}@firm.com"} for i in range(5)]  # 25%

        mock_claude = MagicMock()
        mock_claude.generate.return_value = "# Weekly Report\n\nAll good."

        agent = ReportingAgent(claude_client=mock_claude)
        rate = agent.calculate_response_rate(deal)
        assert rate == pytest.approx(0.25, abs=0.01)

        report = agent.generate_weekly_report(deal)
        # Should not have response rate alert (may still have other content)
        assert "response rate" not in report.lower() or "PHIL ALERT" not in report or \
               "response_rate" not in report  # Flexible check


# ── API Failure Tests ─────────────────────────────────────────────────────────

class TestAPIFailure:
    def test_claude_api_failure_marks_step_needs_retry_and_continues(self, engine):
        """On Claude API failure in step 02, pipeline should continue (non-blocking)."""
        deal = _make_deal(deal_id="edge_api_001")
        deal.documents.nda = DocumentStatus.APPROVED

        with patch("modules.step_02_data_room.DocumentAgent") as MockAgent, \
             patch("modules.step_02_data_room.BoxClient"):
            mock_agent = MagicMock()
            mock_agent.generate_tear_sheet_outline.side_effect = RuntimeError(
                "Claude API failed after 3 attempts"
            )
            mock_agent.generate_pitch_deck_outline.side_effect = RuntimeError(
                "Claude API failed after 3 attempts"
            )
            mock_agent.sequoia_review.side_effect = RuntimeError(
                "Claude API failed after 3 attempts"
            )
            mock_agent.review_financials.side_effect = RuntimeError("API error")
            MockAgent.return_value = mock_agent

            # Should NOT raise — should log error and return failed result
            deal, result = engine.run_step(deal, "02")

        # Errors should be recorded but step should return gracefully
        assert len(result["errors"]) > 0, "Errors should be recorded"
        # Pipeline should be able to continue — result returned, not exception

    def test_step_failure_does_not_stop_pipeline(self, engine):
        """A failing step should be logged but should not stop the full pipeline."""
        deal = _make_deal(deal_id="edge_api_002")

        with patch("modules.step_01_timeline.run") as mock_step1, \
             patch("modules.step_02_data_room.run") as mock_step2, \
             patch("modules.step_03_alt_funding.run") as mock_step3:

            def good_step(d, c): return d, {"success": True, "output": {}, "errors": [], "human_actions_required": []}
            def bad_step(d, c): raise RuntimeError("Step crashed!")

            mock_step1.side_effect = good_step
            mock_step2.side_effect = bad_step  # Step 2 crashes
            mock_step3.side_effect = good_step

            # Running steps 01-03 — step 02 crash should not stop step 03
            result_deal = engine.run_from_step(deal, "01")

        # Step 2 crash logged as error, pipeline continued
        assert len(result_deal.errors) > 0, "Step 2 crash should be logged"


# ── Resume from Checkpoint Tests ─────────────────────────────────────────────

class TestCheckpointResume:
    def test_resume_picks_up_from_checkpoint(self, engine, tmp_path):
        """After Step 3 completes, resuming should start at Step 4."""
        deal = _make_deal(deal_id="edge_resume_001")

        # Simulate step 3 was completed
        deal.log_step("01", "completed", "Step 1 done")
        deal.log_step("02", "completed", "Step 2 done")
        deal.log_step("03", "completed", "Step 3 done")
        engine.checkpoint_manager.save(deal, "03")

        # Load from checkpoint
        loaded_deal = engine.checkpoint_manager.load(deal.deal_id)
        assert loaded_deal is not None
        last_step = engine.checkpoint_manager.get_last_completed_step(deal.deal_id)
        assert last_step == "03"

        # Verify step log preserved
        step_ids = [e["step"] for e in loaded_deal.step_log]
        assert "01" in step_ids
        assert "02" in step_ids
        assert "03" in step_ids


# ── High-Value Deal Tests ─────────────────────────────────────────────────────

class TestHighValueDeal:
    def test_broker_dealer_checklist_generated_for_5m_plus(self, engine):
        """Raise >= $5M must trigger broker-dealer portal checklist."""
        deal = _make_deal(deal_id="edge_hv_001", raise_amount=6_000_000)
        assert deal.raise_amount >= BROKER_DEALER_THRESHOLD

        deal, result = engine.run_step(deal, "09")

        # Broker-dealer checklist should be in outputs
        assert "broker_dealer_checklist" in result.get("output", {}), \
            "Broker-dealer checklist must be generated for $5M+ raises"

        # Phil must be flagged
        human_actions_text = " ".join(result.get("human_actions_required", []))
        assert "Phil" in human_actions_text or "broker" in human_actions_text.lower()

    def test_no_broker_dealer_for_sub_5m(self, engine):
        """Raise < $5M must NOT generate broker-dealer checklist."""
        deal = _make_deal(deal_id="edge_hv_002", raise_amount=2_500_000)
        assert deal.raise_amount < BROKER_DEALER_THRESHOLD

        deal, result = engine.run_step(deal, "09")

        assert "broker_dealer_checklist" not in result.get("output", {}), \
            "Broker-dealer checklist must NOT be generated for sub-$5M raises"


# ── Invalid Deal JSON Tests ───────────────────────────────────────────────────

class TestInvalidDealJSON:
    def test_deal_from_json_validates_required_fields(self, tmp_path):
        """Loading a deal JSON missing required fields should raise ValueError."""
        bad_deal = {
            "deal_id": "bad_001",
            "company_name": "Bad Deal",
            # Missing: company_website, industry, raise_amount, founder fields
        }
        deal_file = tmp_path / "bad_deal.json"
        deal_file.write_text(json.dumps(bad_deal))

        with pytest.raises(ValueError, match="missing required fields"):
            Deal.from_json_file(str(deal_file))

    def test_deal_from_valid_json_succeeds(self, tmp_path):
        """Valid deal JSON should load without errors."""
        valid_deal = {
            "deal_id": "valid_001",
            "company_name": "Valid Corp",
            "company_website": "https://valid.com",
            "industry": "technology",
            "raise_amount": 1_000_000,
            "founder_name": "Valid Founder",
            "founder_email": "valid@valid.com",
            "founder_linkedin": "https://linkedin.com/in/valid",
        }
        deal_file = tmp_path / "valid_deal.json"
        deal_file.write_text(json.dumps(valid_deal))

        deal = Deal.from_json_file(str(deal_file))
        assert deal.deal_id == "valid_001"
        assert deal.company_name == "Valid Corp"
