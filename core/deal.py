"""
core/deal.py — Deal dataclass — the central state object passed through every step.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum
import json
from datetime import datetime


class DealStage(Enum):
    ONBOARDED = "onboarded"
    DATA_ROOM_READY = "data_room_ready"
    ALT_FUNDING_IDENTIFIED = "alt_funding_identified"
    VIDEO_READY = "video_ready"
    OUTREACH_ACTIVE = "outreach_active"
    CAMPAIGNS_LIVE = "campaigns_live"
    INVESTOR_MEETINGS_SCHEDULED = "investor_meetings_scheduled"
    COMMITMENTS_RECEIVED = "commitments_received"
    CLOSED = "closed"


class DocumentStatus(Enum):
    MISSING = "missing"
    DRAFT = "draft"
    APPROVED = "approved"
    DISTRIBUTED = "distributed"


@dataclass
class DealDocuments:
    tear_sheet: DocumentStatus = DocumentStatus.MISSING
    pitch_deck: DocumentStatus = DocumentStatus.MISSING
    financial_projections: DocumentStatus = DocumentStatus.MISSING
    nda: DocumentStatus = DocumentStatus.MISSING
    ppm: DocumentStatus = DocumentStatus.MISSING
    subscription_agreement: DocumentStatus = DocumentStatus.MISSING
    wiring_instructions: DocumentStatus = DocumentStatus.MISSING
    use_of_funds: DocumentStatus = DocumentStatus.MISSING

    def to_dict(self) -> Dict[str, str]:
        return {
            "tear_sheet": self.tear_sheet.value,
            "pitch_deck": self.pitch_deck.value,
            "financial_projections": self.financial_projections.value,
            "nda": self.nda.value,
            "ppm": self.ppm.value,
            "subscription_agreement": self.subscription_agreement.value,
            "wiring_instructions": self.wiring_instructions.value,
            "use_of_funds": self.use_of_funds.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "DealDocuments":
        return cls(
            tear_sheet=DocumentStatus(data.get("tear_sheet", "missing")),
            pitch_deck=DocumentStatus(data.get("pitch_deck", "missing")),
            financial_projections=DocumentStatus(data.get("financial_projections", "missing")),
            nda=DocumentStatus(data.get("nda", "missing")),
            ppm=DocumentStatus(data.get("ppm", "missing")),
            subscription_agreement=DocumentStatus(data.get("subscription_agreement", "missing")),
            wiring_instructions=DocumentStatus(data.get("wiring_instructions", "missing")),
            use_of_funds=DocumentStatus(data.get("use_of_funds", "missing")),
        )

    def missing_documents(self) -> List[str]:
        """Returns list of document names that are MISSING."""
        missing = []
        for field_name in [
            "tear_sheet", "pitch_deck", "financial_projections", "nda",
            "ppm", "subscription_agreement", "wiring_instructions", "use_of_funds"
        ]:
            if getattr(self, field_name) == DocumentStatus.MISSING:
                missing.append(field_name)
        return missing


@dataclass
class Deal:
    # Identity
    deal_id: str
    company_name: str
    company_website: str
    industry: str
    raise_amount: float  # in USD

    # Founder info
    founder_name: str
    founder_email: str
    founder_linkedin: str

    # State
    stage: DealStage = DealStage.ONBOARDED
    documents: DealDocuments = field(default_factory=DealDocuments)

    # Tracking
    investors_contacted: List[Dict] = field(default_factory=list)
    investors_responded: List[Dict] = field(default_factory=list)
    investors_committed: List[Dict] = field(default_factory=list)
    nda_signed_by: List[str] = field(default_factory=list)

    # Campaign state
    outreach_week: int = 0
    campaign_active: bool = False
    meetalfred_campaign_id: Optional[str] = None

    # Metadata
    box_folder_id: Optional[str] = None
    created_at: Optional[str] = None
    last_updated: Optional[str] = None
    step_log: List[Dict] = field(default_factory=list)  # audit trail
    errors: List[str] = field(default_factory=list)

    # Skipped steps tracking
    skipped_steps: List[str] = field(default_factory=list)

    def log_step(self, step: str, status: str, message: str, output: Any = None) -> None:
        """Append a step execution record to the audit trail."""
        self.step_log.append({
            "step": step,
            "status": status,
            "message": message,
            "output": output,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.last_updated = datetime.utcnow().isoformat()

    def add_error(self, error: str) -> None:
        self.errors.append(error)

    def to_dict(self) -> Dict:
        """Serialize Deal to a plain dict (JSON-safe)."""
        return {
            "deal_id": self.deal_id,
            "company_name": self.company_name,
            "company_website": self.company_website,
            "industry": self.industry,
            "raise_amount": self.raise_amount,
            "founder_name": self.founder_name,
            "founder_email": self.founder_email,
            "founder_linkedin": self.founder_linkedin,
            "stage": self.stage.value,
            "documents": self.documents.to_dict(),
            "investors_contacted": self.investors_contacted,
            "investors_responded": self.investors_responded,
            "investors_committed": self.investors_committed,
            "nda_signed_by": self.nda_signed_by,
            "outreach_week": self.outreach_week,
            "campaign_active": self.campaign_active,
            "meetalfred_campaign_id": self.meetalfred_campaign_id,
            "box_folder_id": self.box_folder_id,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "step_log": self.step_log,
            "errors": self.errors,
            "skipped_steps": self.skipped_steps,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Deal":
        """Deserialize Deal from a plain dict."""
        deal = cls(
            deal_id=data["deal_id"],
            company_name=data["company_name"],
            company_website=data["company_website"],
            industry=data["industry"],
            raise_amount=float(data["raise_amount"]),
            founder_name=data["founder_name"],
            founder_email=data["founder_email"],
            founder_linkedin=data["founder_linkedin"],
        )
        deal.stage = DealStage(data.get("stage", "onboarded"))
        deal.documents = DealDocuments.from_dict(data.get("documents", {}))
        deal.investors_contacted = data.get("investors_contacted", [])
        deal.investors_responded = data.get("investors_responded", [])
        deal.investors_committed = data.get("investors_committed", [])
        deal.nda_signed_by = data.get("nda_signed_by", [])
        deal.outreach_week = data.get("outreach_week", 0)
        deal.campaign_active = data.get("campaign_active", False)
        deal.meetalfred_campaign_id = data.get("meetalfred_campaign_id")
        deal.box_folder_id = data.get("box_folder_id")
        deal.created_at = data.get("created_at")
        deal.last_updated = data.get("last_updated")
        deal.step_log = data.get("step_log", [])
        deal.errors = data.get("errors", [])
        deal.skipped_steps = data.get("skipped_steps", [])
        return deal

    @classmethod
    def from_json_file(cls, file_path: str) -> "Deal":
        """Load a Deal from a JSON file, with field validation."""
        with open(file_path, "r") as f:
            data = json.load(f)

        required_fields = [
            "deal_id", "company_name", "company_website", "industry",
            "raise_amount", "founder_name", "founder_email", "founder_linkedin",
        ]
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(f"Invalid deal JSON — missing required fields: {missing}")

        return cls.from_dict(data)

    def company_profile_text(self) -> str:
        """Return a plain-text company summary for use in AI prompts."""
        return (
            f"Company: {self.company_name}\n"
            f"Website: {self.company_website}\n"
            f"Industry: {self.industry}\n"
            f"Raise Amount: ${self.raise_amount:,.0f}\n"
            f"Founder: {self.founder_name} ({self.founder_email})\n"
            f"LinkedIn: {self.founder_linkedin}\n"
        )
