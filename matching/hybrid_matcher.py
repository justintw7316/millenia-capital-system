"""
Hybrid investor-founder matching service.

Pipeline:
1. Hard eligibility filtering
2. Hybrid candidate generation (vector + keyword + warm path boosts)
3. Feature computation
4. Weighted reranking
5. Explainability and approval queue payloads
"""
from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Dict, List, Tuple

from core.deal import Deal
from matching.embedder import LocalHashEmbedder
from matching.profile_builder import build_company_profile_from_deal
from matching.repository import LocalInvestorRepository
from matching.schemas import (
    CompanyProfile,
    InvestorCandidate,
    MatchExplanation,
    MatchFeatures,
    MatchResult,
    MatchRun,
)
from matching.vector_store import InMemoryVectorStore, VectorRecord


DEFAULT_WEIGHTS = {
    "semantic_fit": 0.30,
    "stage_and_check": 0.20,
    "recent_activity": 0.15,
    "portfolio_adjacency": 0.10,
    "geography_fit": 0.10,
    "warm_intro_score": 0.10,
    "data_quality_confidence": 0.05,
}


class HybridMatchingService:
    def __init__(
        self,
        repository: LocalInvestorRepository | None = None,
        embedder: LocalHashEmbedder | None = None,
        vector_store: InMemoryVectorStore | None = None,
    ):
        self.repository = repository or LocalInvestorRepository()
        self.embedder = embedder or LocalHashEmbedder()
        self.vector_store = vector_store or InMemoryVectorStore()

    def run_match(self, deal: Deal, top_k: int = 20, candidate_target: int = 300) -> MatchRun:
        profile = build_company_profile_from_deal(deal)
        all_candidates = self.repository.load_candidates(deal)
        eligible, rejected = self._hard_filter_candidates(profile, all_candidates)

        self._index_candidates(eligible)
        vector_scores = self._vector_candidate_scores(profile, eligible, top_k=min(max(candidate_target, top_k), len(eligible) or top_k))
        keyword_scores = self._keyword_candidate_scores(profile, eligible)
        warm_boosts = {c.investor_id: min(1.0, 0.4 + 0.3 * len(c.warm_intro_paths)) for c in eligible if c.warm_intro_paths}

        stage2_ids = set()
        stage2_ids.update([cid for cid, _ in sorted(vector_scores.items(), key=lambda x: x[1], reverse=True)[:max(top_k * 3, 20)]])
        stage2_ids.update([cid for cid, _ in sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)[:max(top_k * 3, 20)]])
        stage2_ids.update([cid for cid, boost in warm_boosts.items() if boost > 0])

        shortlisted = [c for c in eligible if c.investor_id in stage2_ids] or eligible

        results: List[MatchResult] = []
        for cand in shortlisted:
            features = self._compute_features(profile, cand, vector_scores.get(cand.investor_id, 0.0), keyword_scores.get(cand.investor_id, 0.0))
            final_score = self._final_score(features)
            explanation = self._explain(profile, cand, features, rejected_reason=None)
            results.append(MatchResult(
                investor=cand,
                features=features,
                final_score=final_score,
                explanation=explanation,
                score_weights=DEFAULT_WEIGHTS.copy(),
            ))

        results.sort(key=lambda r: r.final_score, reverse=True)
        for i, r in enumerate(results[:top_k], 1):
            r.rank = i

        top_results = results[:top_k]
        return MatchRun(
            deal_id=deal.deal_id,
            company_name=deal.company_name,
            query_inputs={
                "industry": profile.industry,
                "raise_amount": profile.raise_amount,
                "stage": profile.stage,
                "geography": profile.geography,
                "top_k": top_k,
                "candidate_target": candidate_target,
            },
            model_versions={
                "embedding_model": self.embedder.model_name,
                "reranker": "weighted-rules-v1",
                "vector_store": "in-memory-vector-store-v1",
                "keyword_search": "token-overlap-v1",
            },
            score_weights=DEFAULT_WEIGHTS.copy(),
            candidate_counts={
                "raw_candidates": len(all_candidates),
                "eligible_after_filters": len(eligible),
                "rejected_by_filters": len(rejected),
                "stage2_shortlist": len(shortlisted),
                "final_ranked": len(top_results),
            },
            results=top_results,
            approval_queue={
                "status": "pending_phil_team_review",
                "human_in_loop_controls": [
                    "editable_exclusions",
                    "override_rank",
                    "pin_investor",
                    "mark_do_not_contact",
                    "save_approval_rationale",
                ],
                "recommended_actions": [
                    "Review match reasons and recent signals for top 20",
                    "Approve, reject, or pin investors before Step 07b outreach drafting",
                    "Tag warm-path contacts for Phil/GT follow-up",
                ],
            },
            generated_at=datetime.utcnow().isoformat(),
        )

    def results_to_outreach_records(self, match_run: MatchRun) -> List[dict]:
        out = []
        for r in match_run.results:
            inv = r.investor
            reasons = r.explanation.reasons[:4]
            recent_signals = [s.to_dict() for s in inv.signals[:3]]
            feature_dict = r.features.to_dict()
            fit_score_0_100 = int(round(r.final_score * 100))
            out.append({
                "rank": r.rank,
                "full_name": inv.full_name,
                "firm": inv.firm,
                "title": inv.title,
                "email": inv.email,
                "phone": inv.phone,
                "linkedin_url": inv.linkedin_url,
                "twitter_handle": inv.twitter_handle,
                "website": inv.website,
                "fit_score": fit_score_0_100,
                "investment_thesis": inv.investment_thesis,
                "why_good_fit": "; ".join(reasons) if reasons else "Hybrid matching score indicates strong fit.",
                "portfolio_companies": inv.portfolio_companies,
                "check_size_range": inv.check_size_range,
                "match_features": feature_dict,
                "match_explanation": r.explanation.to_dict(),
                "recent_signals": recent_signals,
                "warm_intro_paths": inv.warm_intro_paths,
                "source_tags": inv.source_tags,
                "score_breakdown": {
                    "final_score": round(r.final_score, 4),
                    "weights": r.score_weights,
                },
                "match_segment": r.explanation.match_segment,
                "data_quality_confidence": inv.data_quality_confidence,
                "last_verified_at": inv.last_verified_at,
            })
        return out

    def _hard_filter_candidates(self, profile: CompanyProfile, candidates: List[InvestorCandidate]) -> Tuple[List[InvestorCandidate], List[Tuple[str, str]]]:
        eligible = []
        rejected = []
        for c in candidates:
            # Fund status
            if c.fund.status != "active":
                rejected.append((c.investor_id, "inactive_fund"))
                continue

            # Sector exclusions
            if any(ex.lower() in profile.industry.lower() for ex in c.fund.sector_exclusions):
                rejected.append((c.investor_id, "sector_exclusion"))
                continue

            # Stage mismatch (soft-block if no stage metadata)
            if c.fund.stage_focus and profile.stage not in c.fund.stage_focus:
                if not (profile.stage == "series_a" and "seed" in c.fund.stage_focus):
                    rejected.append((c.investor_id, "stage_mismatch"))
                    continue

            # Check size compatibility minimum
            if c.fund.check_size_max < max(100_000, int(profile.raise_amount * 0.005)):
                rejected.append((c.investor_id, "check_size_too_small"))
                continue

            # Geography restriction
            if c.fund.geography and not any(g in c.fund.geography for g in profile.geography):
                rejected.append((c.investor_id, "geography_mismatch"))
                continue

            eligible.append(c)
        return eligible, rejected

    def _index_candidates(self, candidates: List[InvestorCandidate]) -> None:
        namespaces = {
            "investor_fund_thesis_chunks": [],
            "investor_partner_bios": [],
            "investor_public_content_chunks": [],
            "investor_portfolio_company_chunks": [],
        }
        for c in candidates:
            base_meta = {
                "entity_id": c.investor_id,
                "entity_type": "investor_partner",
                "fund_id": c.fund.fund_id,
                "partner_id": c.investor_id,
                "industry_tags": c.fund.industry_focus,
                "stage_tags": c.fund.stage_focus,
                "geos": c.fund.geography,
                "confidence": c.data_quality_confidence,
                "visibility": "public",
            }
            namespaces["investor_fund_thesis_chunks"].append(VectorRecord(
                namespace="investor_fund_thesis_chunks",
                record_id=f"{c.investor_id}:fund_thesis",
                vector=self.embedder.embed(c.fund.thesis_text or c.investment_thesis),
                metadata={**base_meta, "source_type": "fund_thesis"},
            ))
            namespaces["investor_partner_bios"].append(VectorRecord(
                namespace="investor_partner_bios",
                record_id=f"{c.investor_id}:partner_bio",
                vector=self.embedder.embed(f"{c.full_name} {c.title} at {c.firm}. {c.investment_thesis}"),
                metadata={**base_meta, "source_type": "partner_bio"},
            ))
            namespaces["investor_portfolio_company_chunks"].append(VectorRecord(
                namespace="investor_portfolio_company_chunks",
                record_id=f"{c.investor_id}:portfolio",
                vector=self.embedder.embed(" ".join(c.portfolio_companies)),
                metadata={**base_meta, "source_type": "portfolio"},
            ))
            public_text = " ".join(s.text for s in c.signals[:5]) or c.investment_thesis
            namespaces["investor_public_content_chunks"].append(VectorRecord(
                namespace="investor_public_content_chunks",
                record_id=f"{c.investor_id}:activity",
                vector=self.embedder.embed(public_text),
                metadata={**base_meta, "source_type": "public_content"},
            ))
        for ns, recs in namespaces.items():
            self.vector_store.upsert(ns, recs)

    def _vector_candidate_scores(self, profile: CompanyProfile, candidates: List[InvestorCandidate], top_k: int) -> Dict[str, float]:
        company_vectors = {
            "fund": self.embedder.embed(profile.text_fields.get("industry_market", "")),
            "partner": self.embedder.embed(profile.text_fields.get("company_core", "")),
            "portfolio": self.embedder.embed(profile.text_fields.get("problem", "")),
            "activity": self.embedder.embed(profile.text_fields.get("raise_thesis", "")),
        }
        ns_map = {
            "fund": "investor_fund_thesis_chunks",
            "partner": "investor_partner_bios",
            "portfolio": "investor_portfolio_company_chunks",
            "activity": "investor_public_content_chunks",
        }
        partials: Dict[str, Dict[str, float]] = {}
        for key, ns in ns_map.items():
            for hit in self.vector_store.query(ns, company_vectors[key], top_k=top_k):
                inv_id = hit["record_id"].split(":")[0]
                partials.setdefault(inv_id, {})[key] = max(partials.get(inv_id, {}).get(key, 0.0), hit["score"])

        scores = {}
        for c in candidates:
            p = partials.get(c.investor_id, {})
            # late fusion
            scores[c.investor_id] = (
                0.35 * p.get("fund", 0.0) +
                0.30 * p.get("partner", 0.0) +
                0.15 * p.get("portfolio", 0.0) +
                0.20 * p.get("activity", 0.0)
            )
        return scores

    def _keyword_candidate_scores(self, profile: CompanyProfile, candidates: List[InvestorCandidate]) -> Dict[str, float]:
        query_tokens = _tokens(
            " ".join([
                profile.industry,
                profile.text_fields.get("problem", ""),
                profile.text_fields.get("industry_market", ""),
                profile.text_fields.get("raise_thesis", ""),
            ])
        )
        scores = {}
        for c in candidates:
            haystack = " ".join([
                c.investment_thesis,
                " ".join(c.fund.industry_focus),
                " ".join(c.portfolio_companies),
                " ".join(s.text for s in c.signals),
            ])
            cand_tokens = _tokens(haystack)
            if not cand_tokens:
                scores[c.investor_id] = 0.0
                continue
            overlap = len(query_tokens & cand_tokens)
            scores[c.investor_id] = min(1.0, overlap / max(6, len(query_tokens)))
        return scores

    def _compute_features(self, profile: CompanyProfile, cand: InvestorCandidate, vector_score: float, keyword_score: float) -> MatchFeatures:
        semantic_fit = min(1.0, 0.8 * vector_score + 0.2 * keyword_score)
        stage_compat = 1.0 if profile.stage in cand.fund.stage_focus else (0.7 if "seed" in cand.fund.stage_focus else 0.3)
        target_check_min = profile.raise_amount * 0.005
        target_check_max = profile.raise_amount * 0.05
        overlap_min = max(target_check_min, cand.fund.check_size_min)
        overlap_max = min(target_check_max, cand.fund.check_size_max)
        if overlap_max <= overlap_min:
            check_compat = 0.2 if cand.fund.check_size_max >= target_check_min * 0.6 else 0.0
        else:
            denom = max(target_check_max - target_check_min, 1)
            check_compat = min(1.0, (overlap_max - overlap_min) / denom + 0.4)
        recent_activity = min(1.0, 0.2 + 0.1 * cand.fund.recent_investment_count_12m)
        industry_token = profile.industry.lower()
        portfolio_hits = sum(1 for p in cand.portfolio_companies if any(tok in p.lower() for tok in industry_token.split()))
        portfolio_adjacency = min(1.0, 0.3 + 0.25 * portfolio_hits) if cand.portfolio_companies else 0.2
        geography_fit = 1.0 if "United States" in cand.fund.geography else 0.5
        warm_intro = min(1.0, 0.4 + 0.3 * len(cand.warm_intro_paths)) if cand.warm_intro_paths else 0.0
        return MatchFeatures(
            semantic_fit=semantic_fit,
            stage_compatibility=stage_compat,
            check_size_compatibility=check_compat,
            recent_activity=recent_activity,
            portfolio_adjacency=portfolio_adjacency,
            geography_fit=geography_fit,
            warm_intro_score=warm_intro,
            data_quality_confidence=max(0.0, min(1.0, cand.data_quality_confidence)),
            keyword_overlap=keyword_score,
        )

    def _final_score(self, f: MatchFeatures) -> float:
        stage_and_check = (f.stage_compatibility + f.check_size_compatibility) / 2
        score = (
            DEFAULT_WEIGHTS["semantic_fit"] * f.semantic_fit
            + DEFAULT_WEIGHTS["stage_and_check"] * stage_and_check
            + DEFAULT_WEIGHTS["recent_activity"] * f.recent_activity
            + DEFAULT_WEIGHTS["portfolio_adjacency"] * f.portfolio_adjacency
            + DEFAULT_WEIGHTS["geography_fit"] * f.geography_fit
            + DEFAULT_WEIGHTS["warm_intro_score"] * f.warm_intro_score
            + DEFAULT_WEIGHTS["data_quality_confidence"] * f.data_quality_confidence
        )
        return max(0.0, min(1.0, score))

    def _explain(self, profile: CompanyProfile, cand: InvestorCandidate, features: MatchFeatures, rejected_reason: str | None) -> MatchExplanation:
        reasons = []
        warnings = []
        if features.semantic_fit >= 0.65:
            reasons.append(f"{profile.industry.title()} thesis alignment across fund thesis and partner signals")
        if features.stage_compatibility >= 0.9:
            reasons.append(f"{profile.stage.replace('_', ' ').title()}-stage focus matches target raise stage")
        if features.check_size_compatibility >= 0.75:
            reasons.append(
                f"Typical checks align with target investor allocation band (${profile.raise_amount*0.005:,.0f}-${profile.raise_amount*0.05:,.0f})"
            )
        if features.recent_activity >= 0.7:
            reasons.append(f"Recent deployment activity proxy is strong ({cand.fund.recent_investment_count_12m} deals in last 12 months)")
        if cand.warm_intro_paths:
            reasons.append(cand.warm_intro_paths[0])
        if features.portfolio_adjacency >= 0.55:
            reasons.append(f"Portfolio adjacency supports relevance ({', '.join(cand.portfolio_companies[:2])})")
        if features.data_quality_confidence < 0.75:
            warnings.append("Data quality confidence is moderate — verify contact details before outreach")
        if not cand.email:
            warnings.append("Missing email — manual research required")
        if not cand.linkedin_url:
            warnings.append("Missing LinkedIn URL — manual research required")

        segment = _segment_for_candidate(cand, profile)
        provenance = []
        for sig in cand.signals[:3]:
            provenance.append({
                "source_type": sig.source_type,
                "source_url": sig.source_url,
                "date": sig.date,
                "confidence": sig.confidence,
            })
        return MatchExplanation(
            reasons=reasons[:5] or ["Hybrid matching score indicates acceptable fit after eligibility filtering."],
            warnings=warnings,
            source_provenance=provenance,
            match_segment=segment,
        )


def _tokens(text: str) -> set:
    toks = re.findall(r"[a-zA-Z0-9_+#.-]+", (text or "").lower())
    stop = {"the", "and", "for", "with", "this", "that", "from", "into", "are", "is", "in", "of", "to", "a", "an"}
    return {t for t in toks if len(t) > 2 and t not in stop}


def _segment_for_candidate(cand: InvestorCandidate, profile: CompanyProfile) -> str:
    thesis = (cand.investment_thesis or "").lower()
    if "infrastructure" in thesis or "developer" in thesis:
        return "ai_infra" if "ai" in profile.industry.lower() else "deep_tech"
    if "application" in thesis or "saas" in thesis:
        return "ai_apps" if "ai" in profile.industry.lower() else "software"
    if cand.warm_intro_paths:
        return "warm_network"
    return "general_early_stage"
