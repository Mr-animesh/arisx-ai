from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CreditProgram:
    provider: str
    program_name: str
    category: str
    credit_amount: str
    validity: str
    eligibility: str
    requires_vc: str          # "Yes" / "No" / "Preferred"
    apply_url: str
    notes: str = ""
    source_site: str = ""

    @property
    def dedup_key(self) -> str:
        """Unique key for deduplication: provider + program_name (lowercased, stripped)."""
        return f"{self.provider.lower().strip()}::{self.program_name.lower().strip()}"

    def to_row(self) -> list:
        return [
            self.provider,
            self.program_name,
            self.category,
            self.credit_amount,
            self.validity,
            self.eligibility,
            self.requires_vc,
            self.apply_url,
            self.notes,
            self.source_site,
        ]

SHEET_HEADERS = [
    "Provider", "Program Name", "Category",
    "Credit Amount", "Validity", "Eligibility",
    "Requires VC?", "Apply URL", "Notes", "Source Site"
]

NEWS_HEADERS = [
    "Title", "Source", "Date", "URL", "Summary"
]

CATEGORIES = {
    "cloud":   "☁️ Cloud Infra",
    "ai":      "🤖 AI / LLM",
    "voice":   "🎙️ Voice / STT/TTS",
    "devtools":"🛠️ Dev Tools",
    "crm":     "📈 CRM / Growth",
    "gpu":     "🖥️ GPU / Hardware",
    "fintech": "🏦 Fintech / Misc",
}
