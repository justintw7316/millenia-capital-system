"""
tests/test_document_agent.py — Tests for DocumentAgent methods.
"""
import pytest
from unittest.mock import MagicMock, patch

from core.deal import Deal, DealDocuments, DocumentStatus
from agents.document_agent import DocumentAgent


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_deal():
    return Deal(
        deal_id="doc_test_001",
        company_name="DocTest Corp",
        company_website="https://doctest.com",
        industry="artificial intelligence",
        raise_amount=3_000_000,
        founder_name="Emma Brown",
        founder_email="emma@doctest.com",
        founder_linkedin="https://linkedin.com/in/emmabrown",
        created_at="2026-02-24",
    )


@pytest.fixture
def mock_claude():
    """Returns a mock ClaudeClient that returns preset responses."""
    mock = MagicMock()
    mock.generate.return_value = "# Tear Sheet\n\nMock content for testing."
    mock.generate_json.return_value = {
        "slides": [
            {"slide_number": i, "title": f"Slide {i}", "key_points": ["point 1"], "content_guidance": ""}
            for i in range(1, 12)
        ]
    }
    return mock


@pytest.fixture
def agent(mock_claude):
    return DocumentAgent(claude_client=mock_claude)


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestTearSheetGeneration:
    def test_generate_tear_sheet_returns_string(self, agent, sample_deal):
        result = agent.generate_tear_sheet_outline(sample_deal)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_tear_sheet_calls_claude(self, agent, sample_deal, mock_claude):
        agent.generate_tear_sheet_outline(sample_deal)
        mock_claude.generate.assert_called_once()
        call_args = mock_claude.generate.call_args[0][0]
        assert sample_deal.company_name in call_args


class TestPitchDeckGeneration:
    def test_pitch_deck_returns_dict_with_slides(self, agent, sample_deal):
        result = agent.generate_pitch_deck_outline(sample_deal)
        assert isinstance(result, dict)
        assert "slides" in result

    def test_pitch_deck_has_11_slides(self, agent, sample_deal):
        result = agent.generate_pitch_deck_outline(sample_deal)
        assert len(result["slides"]) == 11

    def test_pitch_deck_calls_generate_json(self, agent, sample_deal, mock_claude):
        agent.generate_pitch_deck_outline(sample_deal)
        mock_claude.generate_json.assert_called_once()


class TestSequoiaReview:
    def test_sequoia_review_returns_dict(self, agent, sample_deal, mock_claude):
        mock_claude.generate_json.return_value = {
            "grades": {
                "company_purpose": {"score": 8, "notes": "Clear"},
            },
            "overall_score": 7.5,
            "critical_revisions": ["Improve financial projections"],
            "strengths": ["Strong team"],
            "investment_readiness": "needs_work",
        }
        result = agent.sequoia_review(sample_deal)
        assert isinstance(result, dict)
        assert "grades" in result
        assert "overall_score" in result
        assert "investment_readiness" in result

    def test_sequoia_review_includes_all_grade_fields(self, agent, sample_deal, mock_claude):
        mock_claude.generate_json.return_value = {
            "grades": {
                "company_purpose": {"score": 9, "notes": ""},
                "problem_definition": {"score": 8, "notes": ""},
                "solution_differentiation": {"score": 7, "notes": "Needs more detail"},
                "market_size_credibility": {"score": 8, "notes": ""},
                "competitive_positioning": {"score": 6, "notes": "Weak"},
                "team_strength": {"score": 9, "notes": ""},
                "financial_projections": {"score": 5, "notes": "Missing WACC"},
                "overall_investment_thesis": {"score": 7, "notes": ""},
            },
            "overall_score": 7.4,
            "critical_revisions": [],
            "strengths": [],
            "investment_readiness": "needs_work",
        }
        result = agent.sequoia_review(sample_deal)
        assert len(result["grades"]) == 8


class TestFinancialReview:
    def test_financial_review_checks_required_components(self, agent, sample_deal, mock_claude):
        mock_claude.generate_json.return_value = {
            "components": {
                "fcff": {"status": "missing", "notes": "Not provided"},
                "weighted_valuation": {"status": "present", "notes": ""},
                "income_statement": {"status": "present", "notes": ""},
                "assumptions": {"status": "missing", "notes": "Not provided"},
                "balance_sheet": {"status": "incomplete", "notes": "Missing 3-year projection"},
                "wacc": {"status": "missing", "notes": "Not calculated"},
                "market_comparisons": {"status": "present", "notes": ""},
                "book_value": {"status": "missing", "notes": ""},
            },
            "missing_items": ["fcff", "assumptions", "wacc", "book_value"],
            "overall_quality": "insufficient",
            "action_items": ["Add FCFF calculation", "Provide WACC methodology"],
        }
        result = agent.review_financials(sample_deal)
        assert "components" in result
        assert "missing_items" in result
        assert len(result["missing_items"]) > 0
