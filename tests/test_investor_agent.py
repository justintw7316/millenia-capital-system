"""
tests/test_investor_agent.py — Tests for InvestorAgent and CampaignAgent.
"""
import pytest
from unittest.mock import MagicMock

from core.deal import Deal, DocumentStatus, DealDocuments
from agents.investor_agent import InvestorAgent
from agents.campaign_agent import CampaignAgent


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_deal():
    return Deal(
        deal_id="inv_test_001",
        company_name="InvTest AI",
        company_website="https://invtestai.com",
        industry="artificial intelligence",
        raise_amount=2_500_000,
        founder_name="Alice Chen",
        founder_email="alice@invtestai.com",
        founder_linkedin="https://linkedin.com/in/alicechen",
        created_at="2026-02-24",
    )


@pytest.fixture
def mock_investor_list():
    return [
        {
            "rank": i,
            "full_name": f"Investor {i}",
            "firm": f"Firm {i}",
            "title": "Partner",
            "email": f"investor{i}@firm{i}.com",
            "phone": f"+1-415-555-{i:04d}",
            "linkedin_url": f"https://linkedin.com/in/investor{i}",
            "twitter_handle": f"@investor{i}",
            "website": f"https://firm{i}.com",
            "fit_score": 90 - i,
            "investment_thesis": f"AI and software at seed stage",
            "why_good_fit": "Strong thesis alignment",
            "portfolio_companies": ["Company A", "Company B"],
            "check_size_range": "$500K - $5M",
        }
        for i in range(1, 21)  # 20 investors
    ]


@pytest.fixture
def mock_claude_investor(mock_investor_list):
    mock = MagicMock()
    mock.generate_json.return_value = mock_investor_list
    return mock


@pytest.fixture
def investor_agent(mock_claude_investor):
    return InvestorAgent(claude_client=mock_claude_investor)


# ── InvestorAgent Tests ───────────────────────────────────────────────────────

class TestInvestorDiscovery:
    def test_find_investors_returns_list(self, investor_agent, sample_deal):
        result = investor_agent.find_investors(sample_deal)
        assert isinstance(result, list)

    def test_find_investors_returns_up_to_20(self, investor_agent, sample_deal):
        result = investor_agent.find_investors(sample_deal)
        assert len(result) <= 20

    def test_find_investors_sorted_by_fit_score(self, investor_agent, sample_deal):
        result = investor_agent.find_investors(sample_deal)
        if len(result) > 1:
            scores = [inv.get("fit_score", 0) for inv in result]
            assert scores == sorted(scores, reverse=True)

    def test_find_investors_deduplicates_by_email(self, sample_deal):
        """Investors with duplicate emails should be removed."""
        mock = MagicMock()
        # Return list with a duplicate email
        mock.generate_json.return_value = [
            {"rank": 1, "full_name": "Investor A", "firm": "Firm A",
             "email": "duplicate@firm.com", "fit_score": 90},
            {"rank": 2, "full_name": "Investor B (duplicate)", "firm": "Firm B",
             "email": "duplicate@firm.com", "fit_score": 85},
            {"rank": 3, "full_name": "Investor C", "firm": "Firm C",
             "email": "unique@firm.com", "fit_score": 80},
        ]
        agent = InvestorAgent(claude_client=mock)
        result = agent.find_investors(sample_deal)
        emails = [inv.get("email") for inv in result]
        assert len(emails) == len(set(emails))  # No duplicates


class TestInvestorFitScoring:
    def test_score_returns_float_in_range(self, sample_deal):
        mock = MagicMock()
        mock.generate_json.return_value = {
            "fit_score": 0.85,
            "reasoning": "Strong alignment",
            "alignment_factors": ["AI focus", "Seed stage"],
            "misalignment_factors": [],
        }
        agent = InvestorAgent(claude_client=mock)
        investor = {
            "full_name": "Test Investor",
            "firm": "Test Firm",
            "investment_thesis": "AI companies",
            "portfolio_companies": ["CompA"],
            "check_size_range": "$500K-$2M",
        }
        score = agent.score_investor_fit(sample_deal, investor)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_score_clamped_to_valid_range(self, sample_deal):
        """Score > 1.0 or < 0.0 from AI should be clamped."""
        mock = MagicMock()
        mock.generate_json.return_value = {"fit_score": 1.5}  # Out of range
        agent = InvestorAgent(claude_client=mock)
        score = agent.score_investor_fit(sample_deal, {})
        assert score == 1.0  # Clamped


# ── CampaignAgent Tests ───────────────────────────────────────────────────────

class TestOutreachMessageDrafting:
    def test_draft_messages_returns_6_platforms(self, sample_deal):
        mock = MagicMock()
        mock.generate_json.return_value = {
            "investor_name": "Test Investor",
            "investor_firm": "Test Firm",
            "messages": {
                "web_contact_form": {"body": "Test web form message"},
                "linkedin": {"subject": "Test Subject", "body": "Test LinkedIn message"},
                "email": {"subject": "Test Email Subject", "body": "Test email body"},
                "sms": {"body": "Test SMS"},
                "whatsapp": {"body": "Test WhatsApp"},
                "twitter_dm": {"body": "Test Twitter DM"},
            },
        }
        agent = CampaignAgent(claude_client=mock)
        investor = {
            "full_name": "John Doe",
            "firm": "Test VC",
            "why_good_fit": "Strong AI thesis alignment",
        }
        result = agent.draft_outreach_messages(sample_deal, investor)
        assert "messages" in result
        messages = result["messages"]
        expected_platforms = ["web_contact_form", "linkedin", "email", "sms", "whatsapp", "twitter_dm"]
        for platform in expected_platforms:
            assert platform in messages, f"Missing platform: {platform}"

    def test_draft_messages_includes_investor_name(self, sample_deal):
        mock = MagicMock()
        mock.generate_json.return_value = {
            "messages": {
                "web_contact_form": {"body": "Hi Jane"},
                "linkedin": {"subject": "Hi", "body": "Hi Jane"},
                "email": {"subject": "Hi", "body": "Hi Jane"},
                "sms": {"body": "Hi"},
                "whatsapp": {"body": "Hi"},
                "twitter_dm": {"body": "Hi"},
            }
        }
        agent = CampaignAgent(claude_client=mock)
        result = agent.draft_outreach_messages(sample_deal, {"full_name": "Jane Investor", "firm": "Test"})
        assert result["investor_name"] == "Jane Investor"
