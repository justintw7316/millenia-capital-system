"""
Local repository for investor/fund/partner data.

This mirrors the future shape of a Postgres-backed repository but loads from
`data/mock_investors/investors_sample.json` and supplements with Apollo stub data.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List

from core.deal import Deal
from integrations.apollo_client import ApolloClient
from matching.schemas import FundProfile, InvestorCandidate, InvestorSignal
from config import DATA_DIR


_DEFAULT_STAGE_BY_RAISE = [
    (1_500_000, ["pre-seed", "seed"]),
    (5_000_000, ["seed", "series_a"]),
    (20_000_000, ["series_a", "series_b", "growth"]),
]


class LocalInvestorRepository:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = Path(data_dir or DATA_DIR)
        self._apollo = ApolloClient()

    def load_candidates(self, deal: Deal) -> List[InvestorCandidate]:
        base = self._load_sample_investors()
        apollo_candidates = self._apollo_candidates_for_deal(deal)
        merged = _dedupe_candidates(base + apollo_candidates)
        return merged

    def _load_sample_investors(self) -> List[InvestorCandidate]:
        path = self.data_dir / "mock_investors" / "investors_sample.json"
        if not path.exists():
            return []
        with open(path, "r") as f:
            payload = json.load(f)
        out = []
        for idx, raw in enumerate(payload.get("investors", []), 1):
            out.append(_candidate_from_raw(raw, idx, source_tag="mock_seed_dataset"))
        return out

    def _apollo_candidates_for_deal(self, deal: Deal) -> List[InvestorCandidate]:
        contacts = self._apollo.search_investors({
            "industry": deal.industry,
            "location": "United States",
            "title_keywords": ["Partner", "Principal", "Managing Partner"],
            "min_portfolio_size": 5,
        })
        results = []
        for idx, c in enumerate(contacts, 1):
            name = c.get("name", f"Apollo Contact {idx}")
            firm_name = _title_case_firm(c.get("firm") or c.get("website", "Unknown VC"))
            stage_focus = _stage_focus_guess_from_name(firm_name)
            min_chk, max_chk = _check_range_guess_from_title(c.get("title", "Partner"))
            thesis = f"{deal.industry.title()} and technology investments with focus on early-stage opportunities."
            fund = FundProfile(
                fund_id=f"fund_apollo_{idx}",
                name=firm_name,
                stage_focus=stage_focus,
                check_size_min=min_chk,
                check_size_max=max_chk,
                geography=["United States", "Canada"],
                industry_focus=[deal.industry.title(), "Technology"],
                recent_investment_count_12m=4 + (idx % 5),
                thesis_text=thesis,
            )
            signals = [
                InvestorSignal(
                    source_type="apollo_stub",
                    text=f"Profile indicates {c.get('title', 'Partner')} at {firm_name} with {deal.industry} focus.",
                    source_url=c.get("linkedin", ""),
                    date=datetime.utcnow().strftime("%Y-%m-%d"),
                    confidence=0.65,
                ),
                InvestorSignal(
                    source_type="public_post",
                    text=f"Interested in seed-stage {deal.industry} founders with strong GTM discipline.",
                    date=datetime.utcnow().strftime("%Y-%m-%d"),
                    confidence=0.55,
                ),
            ]
            results.append(InvestorCandidate(
                investor_id=f"apollo_{idx}",
                full_name=name,
                firm=fund.name,
                title=c.get("title", "Partner"),
                email=c.get("email", ""),
                phone=c.get("phone", ""),
                linkedin_url=c.get("linkedin", ""),
                twitter_handle=c.get("twitter", ""),
                website=c.get("website", ""),
                fund=fund,
                investment_thesis=thesis,
                portfolio_companies=[f"{deal.industry.title()} Co {idx}", f"Enterprise Tool {idx}"],
                check_size_range=f"${min_chk/1000:.0f}K - ${max_chk/1_000_000:.0f}M",
                signals=signals,
                source_tags=["apollo_stub"],
                warm_intro_paths=[],
                data_quality_confidence=0.72,
                last_verified_at=datetime.utcnow().strftime("%Y-%m-%d"),
                metadata={"lead_preference": "either"},
            ))
        return results


def _candidate_from_raw(raw: dict, idx: int, source_tag: str) -> InvestorCandidate:
    industry_guess = _industry_focus_from_text(raw.get("investment_thesis", "") + " " + raw.get("why_good_fit", ""))
    min_chk, max_chk = _parse_check_range(raw.get("check_size_range", ""))
    fund = FundProfile(
        fund_id=f"fund_seed_{idx}",
        name=raw.get("firm", "Unknown Fund"),
        stage_focus=_stage_focus_guess_from_text(raw.get("investment_thesis", "")),
        check_size_min=min_chk,
        check_size_max=max_chk,
        geography=["United States", "Canada"],
        industry_focus=industry_guess or ["Technology"],
        recent_investment_count_12m=6 + (idx % 4),
        thesis_text=raw.get("investment_thesis", ""),
    )
    signals = [
        InvestorSignal(
            source_type="sample_dataset",
            text=raw.get("why_good_fit", ""),
            source_url=raw.get("linkedin_url", ""),
            date="2026-02-24",
            confidence=0.8,
        ),
        InvestorSignal(
            source_type="portfolio_summary",
            text="; ".join(raw.get("portfolio_companies", [])),
            source_url=raw.get("website", ""),
            date="2026-02-24",
            confidence=0.7,
        ),
    ]
    warm_paths = []
    if "securities" in raw.get("firm", "").lower():
        warm_paths.append("Warm path via GT Securities colleague")
    if any(k in raw.get("firm", "").lower() for k in ["sequoia", "a16z", "khosla"]):
        warm_paths.append("Warm path via Millenia network (prior target list)")
    return InvestorCandidate(
        investor_id=f"seed_{idx}",
        full_name=raw.get("full_name", f"Investor {idx}"),
        firm=raw.get("firm", "Unknown Firm"),
        title=raw.get("title", "Partner"),
        email=raw.get("email", ""),
        phone=raw.get("phone", ""),
        linkedin_url=raw.get("linkedin_url", ""),
        twitter_handle=raw.get("twitter_handle", ""),
        website=raw.get("website", ""),
        fund=fund,
        investment_thesis=raw.get("investment_thesis", ""),
        portfolio_companies=raw.get("portfolio_companies", []),
        check_size_range=raw.get("check_size_range", ""),
        signals=signals,
        source_tags=[source_tag],
        warm_intro_paths=warm_paths,
        data_quality_confidence=0.9 if raw.get("email") and raw.get("linkedin_url") else 0.7,
        last_verified_at="2026-02-24",
        metadata={},
    )


def _dedupe_candidates(candidates: List[InvestorCandidate]) -> List[InvestorCandidate]:
    out = []
    seen = set()
    for c in candidates:
        key = (c.email or "").lower().strip() or f"{c.full_name.lower()}|{c.firm.lower()}"
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def _parse_check_range(text: str) -> tuple[int, int]:
    t = (text or "").replace(",", "").lower()
    nums = []
    for token in t.replace("$", " ").replace("-", " ").split():
        if token.endswith("k"):
            try:
                nums.append(int(float(token[:-1]) * 1_000))
            except ValueError:
                pass
        elif token.endswith("m"):
            try:
                nums.append(int(float(token[:-1]) * 1_000_000))
            except ValueError:
                pass
    if len(nums) >= 2:
        return min(nums), max(nums)
    if len(nums) == 1:
        return nums[0], max(nums[0] * 2, nums[0])
    return 250_000, 3_000_000


def _industry_focus_from_text(text: str) -> List[str]:
    t = (text or "").lower()
    tags = []
    for label, keys in {
        "Artificial Intelligence": ["ai", "machine learning", "ml"],
        "Fintech": ["fintech", "payments", "banking"],
        "Healthtech": ["health", "medtech", "digital health"],
        "Climate Tech": ["climate", "cleantech", "sustainability"],
        "Enterprise Software": ["enterprise", "software", "developer"],
    }.items():
        if any(k in t for k in keys):
            tags.append(label)
    return tags


def _stage_focus_guess_from_text(text: str) -> List[str]:
    t = (text or "").lower()
    stages = []
    for s in ["pre-seed", "seed", "series a", "series b", "growth"]:
        if s in t:
            stages.append(s.replace(" ", "_"))
    return stages or ["seed", "series_a"]


def _stage_focus_guess_from_name(_name: str) -> List[str]:
    return ["seed", "series_a"]


def _check_range_guess_from_title(title: str) -> tuple[int, int]:
    t = (title or "").lower()
    if "principal" in t:
        return 250_000, 3_000_000
    if "managing partner" in t or "general partner" in t:
        return 500_000, 10_000_000
    return 250_000, 5_000_000


def _title_case_firm(raw: str) -> str:
    s = (raw or "").replace(".com", "").replace("https://", "").replace("www.", "")
    parts = [p for p in s.replace("-", " ").split() if p]
    return " ".join(p.capitalize() for p in parts) or "Unknown VC"
